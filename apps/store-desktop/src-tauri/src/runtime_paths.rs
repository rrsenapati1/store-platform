use std::env;
use std::fs;
use std::path::{Path, PathBuf};

pub(crate) const CACHE_DB_FILE_NAME: &str = "store-runtime-cache.sqlite3";
const CACHE_RUNTIME_HOME_ENV: &str = "STORE_RUNTIME_HOME";
const CACHE_RUNTIME_HOME_DIR: &str = "StoreRuntime";

pub(crate) fn runtime_cache_db_path() -> PathBuf {
    runtime_home_dir().join(CACHE_DB_FILE_NAME)
}

pub(crate) fn runtime_home_dir() -> PathBuf {
    if let Ok(value) = env::var(CACHE_RUNTIME_HOME_ENV) {
        let trimmed = value.trim();
        if !trimmed.is_empty() {
            return ensure_dir(Path::new(trimmed));
        }
    }

    if let Ok(local_app_data) = env::var("LOCALAPPDATA") {
        let trimmed = local_app_data.trim();
        if !trimmed.is_empty() {
            return ensure_dir(Path::new(trimmed).join(CACHE_RUNTIME_HOME_DIR));
        }
    }

    ensure_dir(
        env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("."))
            .join(".store-runtime"),
    )
}

pub(crate) fn ensure_dir(path: impl AsRef<Path>) -> PathBuf {
    let path = path.as_ref();
    if let Err(err) = fs::create_dir_all(path) {
        eprintln!("failed to create runtime directory {}: {}", path.display(), err);
    }
    path.to_path_buf()
}

pub(crate) fn resolve_hostname() -> Option<String> {
    for key in ["COMPUTERNAME", "HOSTNAME"] {
        if let Ok(value) = env::var(key) {
            let trimmed = value.trim();
            if !trimmed.is_empty() {
                return Some(trimmed.to_string());
            }
        }
    }

    None
}
