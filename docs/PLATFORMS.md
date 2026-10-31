# Platform compatibility

| Environment | Status |
| --- | --- |
| macOS, Python 3.12–3.14, local filesystem | Supported; CI matrix and local APFS acceptance |
| Linux, Python 3.12–3.14, local filesystem | Supported; CI matrix |
| Native Windows | Unsupported; early console/module entry point exits with guidance |
| Network/shared filesystems, Windows-mounted WSL project/store | Durability/locking not validated |

The native Windows gate is deliberate. The engine depends on `fcntl.flock`,
descriptor-relative no-follow operations, directory fsync, POSIX modes, atomic
replacement and POSIX signal forwarding. Windows needs a separate implementation
and real runner tests for locking, junction/reparse points, sharing/delete flags,
reserved names, case behavior and durability. Simulating `sys.platform` only tests
the early message; it is not Windows validation. No Windows CI success is claimed.

WSL may run the Linux version when both project and store are on its Linux local
filesystem; mixed Windows filesystems are outside the validated contract.

Portable case/Unicode-normalization collisions are rejected on supported hosts.
This does not provide a portable archive/export format or preserve ACLs/xattrs.
