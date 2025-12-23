#!/usr/bin/env python3
"""
Codebase Indexer - Multi-Index Architecture
Fast symbol lookup with isolated local and knowledge repo indexes.

Architecture:
  - LOCAL index: Your project code (always active, default)
  - REPO indexes: Knowledge repos (only queried explicitly)

Usage:
    CODEBASE_ROOT=/path/to/code REPOS_ROOT=/path/to/repos python indexer.py
"""

import os
import re
import json
import time
import hashlib
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

from flask import Flask, request, jsonify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class Location:
    file: str
    line: int
    col: int
    symbol_type: str
    mtime: int

@dataclass
class FileMeta:
    path: str
    mtime: int
    size: int
    language: str
    content_hash: str

@dataclass
class ChangeRecord:
    file: str
    timestamp: int
    change_type: str  # added, modified, deleted
    lines_changed: Optional[List[int]] = None


@dataclass
class IntentRecord:
    """Record of an intent capture from tool usage."""
    timestamp: int
    session_id: str
    tool: str
    files: List[str]
    tags: List[str]


class CodebaseIndex:
    """Single codebase index with inverted index, file metadata, and change log."""

    EXTENSIONS = {
        '.ts': 'typescript', '.tsx': 'typescript',
        '.js': 'javascript', '.jsx': 'javascript', '.mjs': 'javascript',
        '.py': 'python',
        '.rs': 'rust',
        '.go': 'go',
        '.java': 'java',
        '.c': 'c', '.h': 'c',
        '.cpp': 'cpp', '.hpp': 'cpp', '.cc': 'cpp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.cs': 'csharp',
        '.json': 'json',
        '.yaml': 'yaml', '.yml': 'yaml',
        '.toml': 'toml',
        '.md': 'markdown',
    }

    IGNORE_DIRS = {
        'node_modules', '.git', '__pycache__', 'target', 'dist',
        'build', '.next', '.nuxt', 'vendor', 'venv', '.venv',
        '.idea', '.vscode', 'coverage', '.cache', 'repos'
    }

    def __init__(self, root: str, name: str = 'local'):
        self.root = Path(root).resolve()
        self.name = name
        self.session_start = int(time.time())
        self.last_indexed = int(time.time())

        # Core data structures
        self.inverted_index: Dict[str, List[Location]] = defaultdict(list)
        self.files: Dict[str, FileMeta] = {}
        self.changes: List[ChangeRecord] = []

        # Dependency graph
        self.deps_outgoing: Dict[str, List[str]] = defaultdict(list)
        self.deps_incoming: Dict[str, List[str]] = defaultdict(list)

        # Thread safety
        self.lock = threading.RLock()

    def get_language(self, path: Path) -> str:
        return self.EXTENSIONS.get(path.suffix.lower(), 'unknown')

    def should_index(self, path: Path) -> bool:
        """Check if file should be indexed."""
        # Use relative path from index root for ignore checks
        try:
            rel_path = path.relative_to(self.root)
            parts = rel_path.parts
        except ValueError:
            parts = path.parts

        if any(part.startswith('.') for part in parts):
            return False
        if any(ignored in parts for ignored in self.IGNORE_DIRS):
            return False
        return path.suffix.lower() in self.EXTENSIONS

    def tokenize(self, content: str) -> List[Tuple[str, int, int]]:
        """Extract tokens with their positions."""
        tokens = []
        for line_num, line in enumerate(content.split('\n'), 1):
            for match in re.finditer(r'[a-zA-Z_][a-zA-Z0-9_]*', line):
                token = match.group()
                if len(token) >= 2:
                    tokens.append((token, line_num, match.start()))
        return tokens

    def index_file(self, path: Path) -> bool:
        """Index a single file."""
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            stat = path.stat()
            mtime = int(stat.st_mtime)

            rel_path = str(path.relative_to(self.root))
            language = self.get_language(path)
            content_hash = hashlib.md5(content.encode()).hexdigest()[:16]

            with self.lock:
                if rel_path in self.files:
                    if self.files[rel_path].content_hash == content_hash:
                        return False
                    self._remove_file_from_index(rel_path)

                self.files[rel_path] = FileMeta(
                    path=rel_path,
                    mtime=mtime,
                    size=stat.st_size,
                    language=language,
                    content_hash=content_hash
                )

                for token, line, col in self.tokenize(content):
                    loc = Location(
                        file=rel_path,
                        line=line,
                        col=col,
                        symbol_type='token',
                        mtime=mtime
                    )
                    self.inverted_index[token].append(loc)
                    lower = token.lower()
                    if lower != token:
                        self.inverted_index[lower].append(loc)

                self._extract_deps(path, content, language)
                self.last_indexed = int(time.time())

            return True

        except Exception as e:
            print(f"Error indexing {path}: {e}")
            return False

    def _remove_file_from_index(self, rel_path: str):
        """Remove all entries for a file from the index."""
        for token, locations in list(self.inverted_index.items()):
            self.inverted_index[token] = [
                loc for loc in locations if loc.file != rel_path
            ]
            if not self.inverted_index[token]:
                del self.inverted_index[token]

        if rel_path in self.deps_outgoing:
            del self.deps_outgoing[rel_path]
        if rel_path in self.deps_incoming:
            del self.deps_incoming[rel_path]

    def _extract_deps(self, path: Path, content: str, language: str):
        """Extract import/dependency information."""
        rel_path = str(path.relative_to(self.root))
        imports = []

        if language in ('typescript', 'javascript'):
            for match in re.finditer(r'''(?:import\s+.*?from\s+|require\()['"]([^'"]+)['"]''', content):
                imports.append(match.group(1))
        elif language == 'python':
            for match in re.finditer(r'^(?:from\s+(\S+)|import\s+(\S+))', content, re.MULTILINE):
                imports.append(match.group(1) or match.group(2))
        elif language == 'rust':
            for match in re.finditer(r'^(?:use|mod)\s+([a-zA-Z_][a-zA-Z0-9_:]*)', content, re.MULTILINE):
                imports.append(match.group(1))

        if imports:
            self.deps_outgoing[rel_path] = imports
            for imp in imports:
                self.deps_incoming[imp].append(rel_path)

    def full_scan(self):
        """Scan entire codebase."""
        start = time.time()
        count = 0

        for path in self.root.rglob('*'):
            if path.is_file() and self.should_index(path):
                if self.index_file(path):
                    count += 1

        elapsed = time.time() - start
        print(f"[{self.name}] Indexed {count} files in {elapsed:.2f}s ({len(self.inverted_index)} symbols)")

    def record_change(self, path: Path, change_type: str):
        """Record a file change."""
        try:
            rel_path = str(path.relative_to(self.root))
        except ValueError:
            rel_path = str(path)

        with self.lock:
            self.changes.append(ChangeRecord(
                file=rel_path,
                timestamp=int(time.time()),
                change_type=change_type
            ))

    def search(self, query: str, mode: str = 'recent', limit: int = 20) -> List[dict]:
        """Search for a term."""
        results = []

        with self.lock:
            if query in self.inverted_index:
                results.extend(self.inverted_index[query])
            lower = query.lower()
            if lower != query and lower in self.inverted_index:
                results.extend(self.inverted_index[lower])

        seen = set()
        unique = []
        for loc in results:
            key = (loc.file, loc.line)
            if key not in seen:
                seen.add(key)
                unique.append(loc)

        if mode == 'recent':
            unique.sort(key=lambda x: x.mtime, reverse=True)
        else:
            unique.sort(key=lambda x: x.file)

        return [asdict(loc) for loc in unique[:limit]]

    def search_multi(self, terms: List[str], mode: str = 'recent', limit: int = 20) -> List[dict]:
        """Search for multiple terms, rank by density."""
        all_results = []
        for term in terms:
            all_results.extend(self.search(term, mode, limit * 2))

        file_scores: Dict[str, Tuple[int, int]] = {}
        for loc in all_results:
            if loc['file'] not in file_scores:
                file_scores[loc['file']] = (0, loc['mtime'])
            count, mtime = file_scores[loc['file']]
            file_scores[loc['file']] = (count + 1, max(mtime, loc['mtime']))

        sorted_files = sorted(
            file_scores.items(),
            key=lambda x: (x[1][0], x[1][1]),
            reverse=True
        )

        top_files = set(f for f, _ in sorted_files[:limit])
        return [loc for loc in all_results if loc['file'] in top_files][:limit]

    def changes_since(self, since: int) -> List[dict]:
        """Get changes since timestamp."""
        with self.lock:
            return [asdict(c) for c in self.changes if c.timestamp >= since]

    def list_files(self, pattern: Optional[str] = None, mode: str = 'recent', limit: int = 50) -> List[dict]:
        """List files matching pattern."""
        with self.lock:
            results = list(self.files.values())

        if pattern:
            if '*' in pattern:
                regex = pattern.replace('.', r'\.').replace('*', '.*')
                results = [f for f in results if re.search(regex, f.path)]
            else:
                results = [f for f in results if pattern in f.path]

        if mode == 'recent':
            results.sort(key=lambda x: x.mtime, reverse=True)
        else:
            results.sort(key=lambda x: x.path)

        return [asdict(f) for f in results[:limit]]

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            'name': self.name,
            'root': str(self.root),
            'files': len(self.files),
            'symbols': len(self.inverted_index),
            'last_indexed': self.last_indexed
        }

    def clear(self):
        """Clear the index."""
        with self.lock:
            self.inverted_index.clear()
            self.files.clear()
            self.changes.clear()
            self.deps_outgoing.clear()
            self.deps_incoming.clear()


# ============================================================================
# Index Manager - Manages local + repo indexes
# ============================================================================

class IndexManager:
    """Manages multiple isolated indexes: local project + knowledge repos."""

    def __init__(self, local_root: str, repos_root: str):
        self.local_root = Path(local_root).resolve()
        self.repos_root = Path(repos_root).resolve()

        # Create repos directory if needed
        self.repos_root.mkdir(parents=True, exist_ok=True)

        # Local index (your project)
        self.local: CodebaseIndex = CodebaseIndex(local_root, name='local')

        # Repo indexes (knowledge repos)
        self.repos: Dict[str, CodebaseIndex] = {}

        # File watchers
        self.observers: Dict[str, Observer] = {}

        self.lock = threading.RLock()

    def init_local(self):
        """Initialize and scan local index."""
        print(f"Initializing local index: {self.local_root}")
        self.local.full_scan()
        self._start_watcher('local', self.local)

    def init_repos(self):
        """Initialize indexes for existing repos."""
        if not self.repos_root.exists():
            return

        for repo_dir in self.repos_root.iterdir():
            if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                self._load_repo(repo_dir.name)

    def _load_repo(self, name: str) -> Optional[CodebaseIndex]:
        """Load an existing repo into the index."""
        repo_path = self.repos_root / name
        if not repo_path.exists():
            return None

        with self.lock:
            if name in self.repos:
                return self.repos[name]

            print(f"Loading repo index: {name}")
            idx = CodebaseIndex(str(repo_path), name=name)
            idx.full_scan()
            self.repos[name] = idx
            self._start_watcher(name, idx)
            return idx

    def _start_watcher(self, name: str, idx: CodebaseIndex):
        """Start file watcher for an index."""
        handler = IndexerHandler(idx)
        observer = Observer()
        observer.schedule(handler, str(idx.root), recursive=True)
        observer.start()
        self.observers[name] = observer
        print(f"File watcher started for: {name}")

    def _stop_watcher(self, name: str):
        """Stop file watcher for an index."""
        if name in self.observers:
            self.observers[name].stop()
            self.observers[name].join()
            del self.observers[name]

    def add_repo(self, name: str, git_url: str) -> Tuple[bool, str]:
        """Clone a git repo and index it."""
        repo_path = self.repos_root / name

        if repo_path.exists():
            return False, f"Repo '{name}' already exists"

        # Clone the repo
        try:
            print(f"Cloning {git_url} to {repo_path}...")
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', git_url, str(repo_path)],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                return False, f"Git clone failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Git clone timed out"
        except Exception as e:
            return False, f"Git clone error: {e}"

        # Index the repo
        idx = self._load_repo(name)
        if idx:
            return True, f"Repo '{name}' added with {len(idx.files)} files"
        else:
            return False, "Failed to index repo"

    def remove_repo(self, name: str) -> Tuple[bool, str]:
        """Remove a repo and its index."""
        repo_path = self.repos_root / name

        with self.lock:
            # Stop watcher
            self._stop_watcher(name)

            # Remove from index
            if name in self.repos:
                del self.repos[name]

            # Remove files
            if repo_path.exists():
                import shutil
                shutil.rmtree(repo_path)
                return True, f"Repo '{name}' removed"
            else:
                return False, f"Repo '{name}' not found"

    def list_repos(self) -> List[dict]:
        """List all knowledge repos."""
        repos = []
        with self.lock:
            for name, idx in self.repos.items():
                repos.append(idx.get_stats())
        return repos

    def get_repo(self, name: str) -> Optional[CodebaseIndex]:
        """Get a repo index by name."""
        with self.lock:
            return self.repos.get(name)

    def get_local(self) -> CodebaseIndex:
        """Get the local index."""
        return self.local

    def shutdown(self):
        """Stop all watchers."""
        for name in list(self.observers.keys()):
            self._stop_watcher(name)


# ============================================================================
# File Watcher
# ============================================================================

class IndexerHandler(FileSystemEventHandler):
    def __init__(self, index: CodebaseIndex):
        self.index = index

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self.index.should_index(path):
            if self.index.index_file(path):
                self.index.record_change(path, 'modified')

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self.index.should_index(path):
            if self.index.index_file(path):
                self.index.record_change(path, 'added')

    def on_deleted(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        try:
            rel_path = str(path.relative_to(self.index.root))
            with self.index.lock:
                if rel_path in self.index.files:
                    self.index._remove_file_from_index(rel_path)
                    del self.index.files[rel_path]
                    self.index.record_change(path, 'deleted')
        except Exception:
            pass


# ============================================================================
# Intent Index - Semantic layer over tool usage
# ============================================================================

class IntentIndex:
    """
    Bidirectional index for intent tracking.

    Stores:
    - tag -> files: Which files are associated with each intent tag
    - file -> tags: Which intent tags are associated with each file
    - timeline: Chronological list of all intent records
    """

    def __init__(self):
        self.tag_to_files: Dict[str, Set[str]] = defaultdict(set)
        self.file_to_tags: Dict[str, Set[str]] = defaultdict(set)
        self.timeline: List[IntentRecord] = []
        self.session_intents: Dict[str, List[IntentRecord]] = defaultdict(list)
        self.lock = threading.RLock()

    def record(self, tool: str, files: List[str], tags: List[str], session_id: str):
        """Record an intent from a tool use."""
        record = IntentRecord(
            timestamp=int(time.time()),
            session_id=session_id,
            tool=tool,
            files=files,
            tags=tags
        )

        with self.lock:
            # Add to timeline
            self.timeline.append(record)
            self.session_intents[session_id].append(record)

            # Update bidirectional indexes
            for tag in tags:
                for f in files:
                    self.tag_to_files[tag].add(f)
                    self.file_to_tags[f].add(tag)

    def files_for_tag(self, tag: str) -> List[str]:
        """Get files associated with a tag."""
        with self.lock:
            return list(self.tag_to_files.get(tag, set()))

    def tags_for_file(self, file: str) -> List[str]:
        """Get tags associated with a file."""
        with self.lock:
            # Try exact match first, then partial
            if file in self.file_to_tags:
                return list(self.file_to_tags[file])
            # Partial match (filename only)
            for f, tags in self.file_to_tags.items():
                if f.endswith(file) or file in f:
                    return list(tags)
            return []

    def recent(self, since: int = None, limit: int = 50) -> List[dict]:
        """Get recent intent records."""
        with self.lock:
            records = self.timeline
            if since:
                records = [r for r in records if r.timestamp >= since]
            records = records[-limit:]
            return [asdict(r) for r in reversed(records)]

    def session(self, session_id: str) -> List[dict]:
        """Get intent records for a session."""
        with self.lock:
            return [asdict(r) for r in self.session_intents.get(session_id, [])]

    def all_tags(self) -> List[Tuple[str, int]]:
        """Get all tags with file counts, sorted by count."""
        with self.lock:
            return sorted(
                [(tag, len(files)) for tag, files in self.tag_to_files.items()],
                key=lambda x: x[1],
                reverse=True
            )

    def get_stats(self) -> dict:
        """Get intent index statistics."""
        with self.lock:
            return {
                'total_records': len(self.timeline),
                'unique_tags': len(self.tag_to_files),
                'unique_files': len(self.file_to_tags),
                'sessions': len(self.session_intents)
            }


# ============================================================================
# Global Index Manager
# ============================================================================

manager: Optional[IndexManager] = None
intent_index: Optional[IntentIndex] = None


# ============================================================================
# API Endpoints - Local Index (default)
# ============================================================================

@app.route('/health')
def health():
    local = manager.get_local()
    return jsonify({
        'status': 'ok',
        'local': local.get_stats(),
        'repos': [r.get_stats() for r in manager.repos.values()]
    })

@app.route('/symbol')
def symbol_search():
    start = time.time()
    q = request.args.get('q', '')
    mode = request.args.get('mode', 'recent')
    limit = int(request.args.get('limit', 20))

    results = manager.get_local().search(q, mode, limit)

    return jsonify({
        'results': results,
        'index': 'local',
        'ms': (time.time() - start) * 1000
    })

@app.route('/multi', methods=['POST'])
def multi_search():
    start = time.time()
    data = request.json
    terms = data.get('terms', [])
    mode = data.get('mode', 'recent')
    limit = int(data.get('limit', 20))

    results = manager.get_local().search_multi(terms, mode, limit)

    return jsonify({
        'results': results,
        'index': 'local',
        'ms': (time.time() - start) * 1000
    })

@app.route('/files')
def files_search():
    start = time.time()
    pattern = request.args.get('match')
    mode = request.args.get('mode', 'recent')
    limit = int(request.args.get('limit', 50))

    results = manager.get_local().list_files(pattern, mode, limit)

    return jsonify({
        'results': results,
        'index': 'local',
        'ms': (time.time() - start) * 1000
    })

@app.route('/changes')
def changes():
    start = time.time()
    since_param = request.args.get('since', '300')
    local = manager.get_local()

    if since_param == 'session':
        since = local.session_start
    else:
        since = int(time.time()) - int(since_param)

    changes = local.changes_since(since)

    added = [c['file'] for c in changes if c['change_type'] == 'added']
    modified = [{'file': c['file'], 'lines_changed': c.get('lines_changed', [])}
                for c in changes if c['change_type'] == 'modified']
    deleted = [c['file'] for c in changes if c['change_type'] == 'deleted']

    return jsonify({
        'added': added,
        'modified': modified,
        'deleted': deleted,
        'index': 'local',
        'ms': (time.time() - start) * 1000
    })

@app.route('/file')
def file_content():
    start = time.time()
    path = request.args.get('path', '')
    lines = request.args.get('lines')
    symbol = request.args.get('symbol')

    full_path = manager.get_local().root / path
    if not full_path.exists():
        return jsonify({'error': 'File not found'}), 404

    content = full_path.read_text(encoding='utf-8', errors='ignore')
    all_lines = content.split('\n')

    if lines:
        parts = lines.split('-')
        start_l = int(parts[0]) - 1
        end_l = int(parts[1]) if len(parts) > 1 else len(all_lines)
        extracted = '\n'.join(all_lines[start_l:end_l])
        return jsonify({
            'content': extracted,
            'lines': (start_l + 1, end_l),
            'ms': (time.time() - start) * 1000
        })
    elif symbol:
        for i, line in enumerate(all_lines):
            if symbol in line:
                start_l = max(0, i - 5)
                end_l = min(len(all_lines), i + 20)
                extracted = '\n'.join(all_lines[start_l:end_l])
                return jsonify({
                    'content': extracted,
                    'lines': (start_l + 1, end_l),
                    'ms': (time.time() - start) * 1000
                })
        return jsonify({'error': 'Symbol not found'}), 404
    else:
        return jsonify({
            'content': content,
            'lines': (1, len(all_lines)),
            'ms': (time.time() - start) * 1000
        })

@app.route('/deps')
def deps():
    start = time.time()
    file = request.args.get('file')
    direction = request.args.get('direction', 'outgoing')
    local = manager.get_local()

    if not file:
        return jsonify({'error': 'file parameter required'}), 400

    with local.lock:
        if direction == 'outgoing':
            results = local.deps_outgoing.get(file, [])
        else:
            results = local.deps_incoming.get(file, [])

    return jsonify({
        'dependencies': results,
        'direction': direction,
        'ms': (time.time() - start) * 1000
    })

@app.route('/structure')
def structure():
    start = time.time()
    focus = request.args.get('focus', '')
    depth = int(request.args.get('depth', 2))
    local = manager.get_local()

    root = local.root / focus if focus else local.root

    def build_tree(path: Path, current_depth: int) -> dict:
        if current_depth > depth:
            return None

        result = {'name': path.name, 'type': 'dir' if path.is_dir() else 'file'}

        if path.is_dir():
            children = []
            try:
                for child in sorted(path.iterdir()):
                    if child.name.startswith('.'):
                        continue
                    if child.name in CodebaseIndex.IGNORE_DIRS:
                        continue
                    subtree = build_tree(child, current_depth + 1)
                    if subtree:
                        children.append(subtree)
            except PermissionError:
                pass
            result['children'] = children

        return result

    tree = build_tree(root, 0)

    return jsonify({
        'tree': tree,
        'ms': (time.time() - start) * 1000
    })


# ============================================================================
# API Endpoints - Repo Management
# ============================================================================

@app.route('/repos', methods=['GET'])
def list_repos():
    """List all knowledge repos."""
    return jsonify({
        'repos': manager.list_repos()
    })

@app.route('/repos', methods=['POST'])
def add_repo():
    """Add a new knowledge repo."""
    data = request.json
    name = data.get('name')
    url = data.get('url')

    if not name or not url:
        return jsonify({'error': 'name and url required'}), 400

    # Sanitize name
    name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    if not name:
        return jsonify({'error': 'Invalid repo name'}), 400

    success, message = manager.add_repo(name, url)

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 400

@app.route('/repos/<name>', methods=['DELETE'])
def remove_repo(name):
    """Remove a knowledge repo."""
    success, message = manager.remove_repo(name)

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 404


# ============================================================================
# API Endpoints - Repo Search (isolated)
# ============================================================================

@app.route('/repo/<name>/symbol')
def repo_symbol_search(name):
    """Search in a specific repo only."""
    start = time.time()

    repo = manager.get_repo(name)
    if not repo:
        return jsonify({'error': f"Repo '{name}' not found"}), 404

    q = request.args.get('q', '')
    mode = request.args.get('mode', 'recent')
    limit = int(request.args.get('limit', 20))

    results = repo.search(q, mode, limit)

    return jsonify({
        'results': results,
        'index': name,
        'ms': (time.time() - start) * 1000
    })

@app.route('/repo/<name>/multi', methods=['POST'])
def repo_multi_search(name):
    """Multi-term search in a specific repo only."""
    start = time.time()

    repo = manager.get_repo(name)
    if not repo:
        return jsonify({'error': f"Repo '{name}' not found"}), 404

    data = request.json
    terms = data.get('terms', [])
    mode = data.get('mode', 'recent')
    limit = int(data.get('limit', 20))

    results = repo.search_multi(terms, mode, limit)

    return jsonify({
        'results': results,
        'index': name,
        'ms': (time.time() - start) * 1000
    })

@app.route('/repo/<name>/files')
def repo_files(name):
    """List files in a specific repo."""
    start = time.time()

    repo = manager.get_repo(name)
    if not repo:
        return jsonify({'error': f"Repo '{name}' not found"}), 404

    pattern = request.args.get('match')
    mode = request.args.get('mode', 'recent')
    limit = int(request.args.get('limit', 50))

    results = repo.list_files(pattern, mode, limit)

    return jsonify({
        'results': results,
        'index': name,
        'ms': (time.time() - start) * 1000
    })

@app.route('/repo/<name>/file')
def repo_file_content(name):
    """Get file content from a specific repo."""
    start = time.time()

    repo = manager.get_repo(name)
    if not repo:
        return jsonify({'error': f"Repo '{name}' not found"}), 404

    path = request.args.get('path', '')
    lines = request.args.get('lines')

    full_path = repo.root / path
    if not full_path.exists():
        return jsonify({'error': 'File not found'}), 404

    content = full_path.read_text(encoding='utf-8', errors='ignore')
    all_lines = content.split('\n')

    if lines:
        parts = lines.split('-')
        start_l = int(parts[0]) - 1
        end_l = int(parts[1]) if len(parts) > 1 else len(all_lines)
        extracted = '\n'.join(all_lines[start_l:end_l])
        return jsonify({
            'content': extracted,
            'lines': (start_l + 1, end_l),
            'index': name,
            'ms': (time.time() - start) * 1000
        })
    else:
        return jsonify({
            'content': content,
            'lines': (1, len(all_lines)),
            'index': name,
            'ms': (time.time() - start) * 1000
        })

@app.route('/repo/<name>/deps')
def repo_deps(name):
    """Get dependencies from a specific repo."""
    start = time.time()

    repo = manager.get_repo(name)
    if not repo:
        return jsonify({'error': f"Repo '{name}' not found"}), 404

    file = request.args.get('file')
    direction = request.args.get('direction', 'outgoing')

    if not file:
        return jsonify({'error': 'file parameter required'}), 400

    with repo.lock:
        if direction == 'outgoing':
            results = repo.deps_outgoing.get(file, [])
        else:
            results = repo.deps_incoming.get(file, [])

    return jsonify({
        'dependencies': results,
        'direction': direction,
        'index': name,
        'ms': (time.time() - start) * 1000
    })


# ============================================================================
# API Endpoints - Pattern Search (Agent-driven AC)
# ============================================================================

@app.route('/pattern', methods=['POST'])
def pattern_search():
    """
    Agent-driven multi-pattern search with AC.

    Agent defines the patterns - no corpus needed.

    POST body:
    {
        "patterns": {
            "function_def": "def\\s+handleAuth\\s*\\(",
            "function_call": "handleAuth\\s*\\("
        },
        "repo": "flask",        # optional: search specific repo (default: local)
        "since": 604800,        # optional: only files modified in last N seconds
        "limit": 50             # optional: max results per pattern
    }
    """
    start = time.time()
    data = request.json

    patterns = data.get('patterns', {})
    repo_name = data.get('repo')  # None = local
    since = data.get('since')  # seconds ago
    limit = data.get('limit', 50)

    if not patterns:
        return jsonify({'error': 'patterns required'}), 400

    # Get the right index
    if repo_name:
        idx = manager.get_repo(repo_name)
        if not idx:
            return jsonify({'error': f"Repo '{repo_name}' not found"}), 404
    else:
        idx = manager.get_local()

    # Compile patterns
    compiled = {}
    for label, pattern in patterns.items():
        try:
            compiled[label] = re.compile(pattern, re.MULTILINE)
        except re.error as e:
            return jsonify({'error': f"Invalid pattern '{label}': {e}"}), 400

    # Time filter
    since_ts = None
    if since:
        since_ts = time.time() - int(since)

    # Search files
    results = {label: [] for label in patterns}
    files_searched = 0
    files_matched = 0

    with idx.lock:
        for rel_path, meta in idx.files.items():
            # Time filter
            if since_ts and meta.mtime < since_ts:
                continue

            files_searched += 1
            full_path = idx.root / rel_path

            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            file_matched = False
            lines = content.split('\n')

            for label, regex in compiled.items():
                if len(results[label]) >= limit:
                    continue

                for match in regex.finditer(content):
                    # Find line number
                    line_start = content.count('\n', 0, match.start()) + 1
                    line_text = lines[line_start - 1].strip()[:80]

                    results[label].append({
                        'file': rel_path,
                        'line': line_start,
                        'match': match.group()[:100],
                        'context': line_text
                    })
                    file_matched = True

                    if len(results[label]) >= limit:
                        break

            if file_matched:
                files_matched += 1

    elapsed = (time.time() - start) * 1000

    return jsonify({
        'results': results,
        'stats': {
            'files_searched': files_searched,
            'files_matched': files_matched,
            'ms': elapsed
        },
        'index': repo_name or 'local'
    })


@app.route('/repo/<name>/pattern', methods=['POST'])
def repo_pattern_search(name):
    """Pattern search in a specific repo."""
    start = time.time()
    data = request.json or {}
    data['repo'] = name

    # Reuse the main pattern search
    repo = manager.get_repo(name)
    if not repo:
        return jsonify({'error': f"Repo '{name}' not found"}), 404

    patterns = data.get('patterns', {})
    since = data.get('since')
    limit = data.get('limit', 50)

    if not patterns:
        return jsonify({'error': 'patterns required'}), 400

    # Compile patterns
    compiled = {}
    for label, pattern in patterns.items():
        try:
            compiled[label] = re.compile(pattern, re.MULTILINE)
        except re.error as e:
            return jsonify({'error': f"Invalid pattern '{label}': {e}"}), 400

    since_ts = None
    if since:
        since_ts = time.time() - int(since)

    results = {label: [] for label in patterns}
    files_searched = 0
    files_matched = 0

    with repo.lock:
        for rel_path, meta in repo.files.items():
            if since_ts and meta.mtime < since_ts:
                continue

            files_searched += 1
            full_path = repo.root / rel_path

            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            file_matched = False
            lines = content.split('\n')

            for label, regex in compiled.items():
                if len(results[label]) >= limit:
                    continue

                for match in regex.finditer(content):
                    line_start = content.count('\n', 0, match.start()) + 1
                    line_text = lines[line_start - 1].strip()[:80]

                    results[label].append({
                        'file': rel_path,
                        'line': line_start,
                        'match': match.group()[:100],
                        'context': line_text
                    })
                    file_matched = True

                    if len(results[label]) >= limit:
                        break

            if file_matched:
                files_matched += 1

    elapsed = (time.time() - start) * 1000

    return jsonify({
        'results': results,
        'stats': {
            'files_searched': files_searched,
            'files_matched': files_matched,
            'ms': elapsed
        },
        'index': name
    })


# ============================================================================
# API Endpoints - Intent Tracking
# ============================================================================

@app.route('/intent', methods=['POST'])
def record_intent():
    """
    Record an intent from tool usage.

    POST body:
    {
        "tool": "Edit",
        "files": ["/path/to/file.py"],
        "tags": ["#authentication", "#editing"],
        "session_id": "abc123"
    }
    """
    data = request.json

    tool = data.get('tool', 'unknown')
    files = data.get('files', [])
    tags = data.get('tags', [])
    session_id = data.get('session_id', 'unknown')

    intent_index.record(tool, files, tags, session_id)

    return jsonify({'success': True})


@app.route('/intent/tags')
def intent_tags():
    """Get all intent tags with counts."""
    tags = intent_index.all_tags()
    return jsonify({
        'tags': [{'tag': t, 'count': c} for t, c in tags]
    })


@app.route('/intent/files')
def intent_files_for_tag():
    """Get files associated with a tag."""
    tag = request.args.get('tag', '')
    if not tag.startswith('#'):
        tag = '#' + tag

    files = intent_index.files_for_tag(tag)
    return jsonify({
        'tag': tag,
        'files': files
    })


@app.route('/intent/file')
def intent_tags_for_file():
    """Get tags associated with a file."""
    file = request.args.get('path', '')
    tags = intent_index.tags_for_file(file)
    return jsonify({
        'file': file,
        'tags': tags
    })


@app.route('/intent/recent')
def intent_recent():
    """Get recent intent records."""
    since = request.args.get('since')
    limit = int(request.args.get('limit', 50))

    since_ts = None
    if since:
        since_ts = int(time.time()) - int(since)

    records = intent_index.recent(since_ts, limit)
    return jsonify({
        'records': records,
        'stats': intent_index.get_stats()
    })


@app.route('/intent/session')
def intent_session():
    """Get intent records for a session."""
    session_id = request.args.get('id', '')
    records = intent_index.session(session_id)
    return jsonify({
        'session_id': session_id,
        'records': records
    })


@app.route('/intent/stats')
def intent_stats():
    """Get intent index statistics."""
    return jsonify(intent_index.get_stats())


# ============================================================================
# Main
# ============================================================================

def main():
    global manager, intent_index

    codebase_root = os.environ.get('CODEBASE_ROOT', '.')
    repos_root = os.environ.get('REPOS_ROOT', './repos')
    port = int(os.environ.get('PORT', 9999))

    print("=" * 60)
    print("aOa Index Service - Multi-Index Architecture")
    print("=" * 60)

    # Initialize intent index
    intent_index = IntentIndex()
    print("Intent index initialized")
    print(f"Local codebase: {codebase_root}")
    print(f"Repos directory: {repos_root}")
    print()

    # Create index manager
    manager = IndexManager(codebase_root, repos_root)

    # Initialize indexes
    manager.init_local()
    manager.init_repos()

    print()
    print(f"Local: {len(manager.local.files)} files, {len(manager.local.inverted_index)} symbols")
    print(f"Repos: {len(manager.repos)} knowledge repos loaded")
    print()

    try:
        print(f"Listening on http://0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, threaded=True)
    finally:
        manager.shutdown()


if __name__ == '__main__':
    main()
