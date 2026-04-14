use crate::runtime_release::{resolve_release_profile, CONTROL_PLANE_BASE_URL_ENV};

pub(crate) fn resolve_control_plane_base_url() -> String {
    resolve_release_profile()
        .map(|resolved| resolved.profile.control_plane_base_url)
        .unwrap_or_else(|_| "http://127.0.0.1:8000".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime_release::{load_bundled_release_profile, runtime_release_env_test_guard};
    use std::env;

    #[test]
    fn uses_bundled_release_profile_when_env_is_missing() {
        let _guard = runtime_release_env_test_guard()
            .lock()
            .expect("lock release env test guard");
        unsafe {
            env::remove_var(CONTROL_PLANE_BASE_URL_ENV);
        }
        let bundled = load_bundled_release_profile().expect("load bundled release profile");
        assert_eq!(
            resolve_control_plane_base_url(),
            bundled.control_plane_base_url
        );
    }

    #[test]
    fn trims_whitespace_and_trailing_slash_from_local_override() {
        let _guard = runtime_release_env_test_guard()
            .lock()
            .expect("lock release env test guard");
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
