use std::env;

pub(crate) const CONTROL_PLANE_BASE_URL_ENV: &str = "STORE_CONTROL_PLANE_BASE_URL";
pub(crate) const DEFAULT_CONTROL_PLANE_BASE_URL: &str = "http://127.0.0.1:8000";

fn normalize_base_url(value: &str) -> Option<String> {
    let normalized = value.trim().trim_end_matches('/');
    if normalized.is_empty() {
        return None;
    }
    Some(normalized.to_string())
}

pub(crate) fn resolve_control_plane_base_url() -> String {
    if let Ok(value) = env::var(CONTROL_PLANE_BASE_URL_ENV) {
        if let Some(normalized) = normalize_base_url(&value) {
            return normalized;
        }
    }

    DEFAULT_CONTROL_PLANE_BASE_URL.to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn uses_default_control_plane_base_url_when_env_is_missing() {
        unsafe {
            env::remove_var(CONTROL_PLANE_BASE_URL_ENV);
        }
        assert_eq!(
            resolve_control_plane_base_url(),
            DEFAULT_CONTROL_PLANE_BASE_URL.to_string()
        );
    }

    #[test]
    fn trims_whitespace_and_trailing_slash_from_env_override() {
        unsafe {
            env::set_var(CONTROL_PLANE_BASE_URL_ENV, " https://control.acme.local/ ");
        }
        assert_eq!(
            resolve_control_plane_base_url(),
            "https://control.acme.local".to_string()
        );
        unsafe {
            env::remove_var(CONTROL_PLANE_BASE_URL_ENV);
        }
    }
}
