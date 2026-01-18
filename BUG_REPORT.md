# aOa System Bugs and Issues Report

**Date:** 2026-01-18
**Branch:** claude/identify-system-bugs-8hPA2
**Analysis Type:** Comprehensive system audit

## Executive Summary

This report identifies bugs, issues, and potential improvements found during a systematic review of the aOa codebase. Issues are categorized by severity and impact.

---

## 🔴 Critical Issues

### 1. Missing `.env` File for Docker Compose
**File:** `/docker-compose.yml` (references `.env`)
**Issue:** The `docker-compose.yml` file expects a `.env` file with critical environment variables (`PROJECTS_ROOT`, `GATEWAY_PORT`, `CODEBASE_PATH`), but this file is not included in the repository.

**Impact:**
- Docker Compose deployment will fail or use undefined variables
- Users cannot run the multi-container setup without manually creating `.env`

**Recommendation:**
- Create `.env.example` template with default values
- Add documentation about required environment variables
- Update `install.sh` to create `.env` if missing

**Example `.env.example`:**
```bash
# aOa Environment Configuration
PROJECTS_ROOT=${HOME}
GATEWAY_PORT=8080
CODEBASE_PATH=.
```

### 2. Missing Execute Permission on Hook
**File:** `plugin/hooks/aoa-auto-outline.py`
**Issue:** The file is missing execute (`+x`) permissions, while all other Python hooks have them.

**Current permissions:**
```
-rw-r--r-- plugin/hooks/aoa-auto-outline.py     # Missing +x
-rwxr-xr-x plugin/hooks/aoa-intent-capture.py   # Correct
-rwxr-xr-x plugin/hooks/aoa-intent-prefetch.py  # Correct
-rwxr-xr-x plugin/hooks/aoa-predict-context.py  # Correct
-rwxr-xr-x plugin/hooks/aoa-intent-prefetch.py  # Correct
-rwxr-xr-x plugin/hooks/aoa-intent-summary.py   # Correct
```

**Impact:**
- Hook will fail to execute when called by Claude Code
- Auto-outline functionality will be broken

**Fix:**
```bash
chmod +x plugin/hooks/aoa-auto-outline.py
```

---

## 🟡 High Priority Issues

### 3. Bare Exception Clause
**File:** `services/proxy/git_proxy.py:315`
**Issue:** Using bare `except:` clause without specifying exception type.

```python
try:
    size_mb = sum(
        f.stat().st_size for f in repo_dir.rglob("*") if f.is_file()
    ) / (1024 * 1024)
except:  # ❌ Bare except - bad practice
    size_mb = 0
```

**Impact:**
- Catches ALL exceptions including KeyboardInterrupt, SystemExit
- Makes debugging harder
- Can hide critical errors

**Fix:**
```python
except (OSError, PermissionError) as e:
    size_mb = 0
```

### 4. Resource Leaks - urlopen Without Context Manager
**Files:**
- `services/hooks/predict-context.py:159`
- `services/hooks/intent-capture.py:257`
- `services/hooks/intent-capture.py:398`

**Issue:** Using `urlopen()` without context manager in "fire and forget" HTTP requests.

```python
# Current (potential resource leak)
urlopen(req, timeout=1)

# Should be
with urlopen(req, timeout=1) as resp:
    pass  # Fire and forget
```

**Impact:**
- Can cause file descriptor leaks over time
- May exhaust system resources in long-running sessions
- While marked "fire and forget", still creates unclosed connections

**Fix:** Use context manager even for fire-and-forget requests.

### 5. Missing Context Files on Fresh Install
**Files:** `.context/BOARD.md`, `.context/CURRENT.md`
**Issue:** The CLAUDE.md instructions reference context files that don't exist in the repository.

**From CLAUDE.md:**
```markdown
**All agents MUST read context files before exploring the codebase.**

When spawning any agent, instruct it to first read:
1. `.context/BOARD.md` - Current focus, active tasks, blockers
2. `.context/CURRENT.md` - Session context, recent decisions
```

**Impact:**
- First-time users will encounter file-not-found errors
- Agents cannot read required context
- Breaks documented workflow

**Recommendation:**
- Create template context files in repository
- Add to `.gitignore` but provide `.example` versions
- Update documentation to note these are user-maintained

---

## 🟢 Medium Priority Issues

### 6. Redis Import Inside Functions
**File:** `services/index/indexer.py:1711, 1813`
**Issue:** Redis module imported inside functions rather than at module level.

```python
def some_function():
    import redis  # ❌ Import inside function
    r = redis.from_url(...)
```

**Impact:**
- Less efficient (re-imports on each call)
- Harder to mock in tests
- Not a critical bug but poor practice

**Fix:** Move imports to module level.

### 7. TODO Comment - Unimplemented Feature
**File:** `services/index/indexer.py:3266`
**Issue:** TODO comment indicates missing per-project Redis key prefixing.

```python
# TODO: Implement per-project Redis key prefixing for metrics
```

**Impact:**
- Multiple projects may share/overwrite metrics in Redis
- Not isolated as advertised in documentation

**Recommendation:** Implement project-scoped Redis keys or document current limitation.

---

## 🔵 Low Priority / Style Issues

### 8. Inconsistent Error Handling Patterns
**Various files**
**Issue:** Mix of error handling styles:
- Some use specific exceptions
- Some use bare `Exception`
- Some use `pass` for silent failures
- Some log errors

**Recommendation:** Establish consistent error handling pattern across codebase.

### 9. No Explicit Python Version Check
**Issue:** Code uses Python 3.11 features (from Dockerfile) but doesn't validate version at runtime.

**Impact:**
- Silent failures on Python < 3.11
- Confusing errors for users with older Python

**Recommendation:** Add version check in main services:
```python
import sys
if sys.version_info < (3, 11):
    print("Error: Python 3.11 or higher required")
    sys.exit(1)
```

---

## 📋 Configuration Issues

### 10. Hardcoded Localhost URLs
**Files:** Multiple hook files
**Issue:** Services assume `localhost:8080` without checking if services are actually running locally vs Docker.

```bash
AOA_URL="${AOA_URL:-http://localhost:8080}"
```

**Impact:**
- May not work in all deployment scenarios
- No graceful handling when services are on different hosts

**Current mitigation:** Environment variable override available (`AOA_URL`)
**Status:** Acceptable with documentation

---

## 🛡️ Security Considerations

### 11. Git Command Execution
**File:** `services/proxy/git_proxy.py`
**Status:** ✅ SECURE - Well implemented

**Review findings:**
- Uses `subprocess.run()` with array arguments (prevents shell injection)
- Validates repository names
- Has whitelist for allowed hosts
- Implements timeouts and size limits
- Good security practices overall

### 12. Path Traversal Protection
**File:** `services/index/indexer.py`
**Status:** ✅ SECURE

**Review findings:**
- Uses `Path.resolve()` to normalize paths
- Validates paths are within project boundaries
- Good use of pathlib for safe path operations

---

## 📊 Summary Statistics

| Severity | Count | Fixed | Remaining |
|----------|-------|-------|-----------|
| Critical | 2     | 0     | 2         |
| High     | 5     | 0     | 5         |
| Medium   | 2     | 0     | 2         |
| Low      | 2     | 0     | 2         |
| **Total**| **11**| **0** | **11**    |

---

## 🔧 Recommended Fixes Priority

1. **Immediate (before next release):**
   - Fix execute permissions on `aoa-auto-outline.py`
   - Create `.env.example` file
   - Fix bare except clause in `git_proxy.py`

2. **Short-term (next sprint):**
   - Fix `urlopen` resource leaks
   - Create template context files
   - Add Python version validation

3. **Medium-term (next version):**
   - Implement per-project Redis key isolation
   - Move Redis imports to module level
   - Standardize error handling

4. **Long-term (backlog):**
   - Improve error handling consistency
   - Enhanced deployment flexibility

---

## ✅ Things That Work Well

**Positive findings:**
- Excellent use of threading locks (RLock) for thread safety
- Good division-by-zero protection in metrics calculations
- Proper use of `subprocess.run()` for command execution
- Strong security model (network isolation, whitelisting)
- Good error handling in file operations (IOError, PermissionError)
- Comprehensive documentation
- Clean separation of concerns

---

## 🎯 Next Steps

1. Review and prioritize fixes
2. Create GitHub issues for tracking
3. Assign owners for critical fixes
4. Update documentation for workarounds
5. Add regression tests for fixed bugs

---

**Report Generated By:** Claude Code Bug Analysis
**Review Status:** Ready for team review
