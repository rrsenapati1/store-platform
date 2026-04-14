use serde::{Deserialize, Serialize};
use std::env;
#[cfg(test)]
use std::sync::{Mutex, OnceLock};

include!(concat!(env!("OUT_DIR"), "/runtime_release_profile.rs"));

pub(crate) const CONTROL_PLANE_BASE_URL_ENV: &str = "STORE_CONTROL_PLANE_BASE_URL";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeReleaseProfile {
    pub environment: String,
    pub control_plane_base_url: String,
    pub updater_endpoint: Option<String>,
    pub updater_pubkey: Option<String>,
    pub allow_local_control_plane_override: bool,
    pub allow_downgrade_updates: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResolvedStoreRuntimeReleaseProfile {
    pub profile: StoreRuntimeReleaseProfile,
    pub source: StoreRuntimeReleaseProfileSource,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StoreRuntimeReleaseProfileSource {
    Bundled,
    BundledWithLocalOverride,
}

impl StoreRuntimeReleaseProfileSource {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Bundled => "bundled",
            Self::BundledWithLocalOverride => "bundled_with_local_override",
        }
    }
}

fn normalize_non_empty(value: &str) -> Option<String> {
    let normalized = value.trim().trim_end_matches('/');
    if normalized.is_empty() {
        return None;
    }
    Some(normalized.to_string())
}

fn parse_release_profile(raw: &str) -> Result<StoreRuntimeReleaseProfile, String> {
    let mut profile = serde_json::from_str::<StoreRuntimeReleaseProfile>(raw).map_err(|error| error.to_string())?;
    profile.environment = normalize_non_empty(&profile.environment)
        .ok_or_else(|| "release profile environment is required".to_string())?;
    profile.control_plane_base_url = normalize_non_empty(&profile.control_plane_base_url)
        .ok_or_else(|| "release profile control-plane base URL is required".to_string())?;
    profile.updater_endpoint = profile
        .updater_endpoint
        .as_deref()
        .and_then(normalize_non_empty);
    profile.updater_pubkey = profile.updater_pubkey.as_deref().and_then(normalize_non_empty);
    Ok(profile)
}

pub(crate) fn load_bundled_release_profile() -> Result<StoreRuntimeReleaseProfile, String> {
    parse_release_profile(BUNDLED_RELEASE_PROFILE_JSON)
}

pub(crate) fn resolve_release_profile() -> Result<ResolvedStoreRuntimeReleaseProfile, String> {
    let mut profile = load_bundled_release_profile()?;
    let mut source = StoreRuntimeReleaseProfileSource::Bundled;

    if profile.allow_local_control_plane_override {
        if let Ok(value) = env::var(CONTROL_PLANE_BASE_URL_ENV) {
            if let Some(normalized) = normalize_non_empty(&value) {
                profile.control_plane_base_url = normalized;
                source = StoreRuntimeReleaseProfileSource::BundledWithLocalOverride;
            }
        }
    }

    Ok(ResolvedStoreRuntimeReleaseProfile { profile, source })
}

#[cfg(test)]
pub(crate) fn runtime_release_env_test_guard() -> &'static Mutex<()> {
    static GUARD: OnceLock<Mutex<()>> = OnceLock::new();
    GUARD.get_or_init(|| Mutex::new(()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_and_normalizes_release_profile() {
        let _guard = runtime_release_env_test_guard()
            .lock()
            .expect("lock release env test guard");
        let profile = parse_release_profile(
            r#"{
              "environment":" staging ",
              "control_plane_base_url":" https://control.acme.local/ ",
              "updater_endpoint":" https://updates.acme.local/latest.json/ ",
              "updater_pubkey":"  pubkey-value  ",
              "allow_local_control_plane_override":false,
              "allow_downgrade_updates":false
            }"#,
        )
        .expect("parse release profile");

        assert_eq!(profile.environment, "staging");
        assert_eq!(profile.control_plane_base_url, "https://control.acme.local");
        assert_eq!(
            profile.updater_endpoint.as_deref(),
            Some("https://updates.acme.local/latest.json")
        );
        assert_eq!(profile.updater_pubkey.as_deref(), Some("pubkey-value"));
    }

    #[test]
    fn bundled_release_profile_is_valid() {
        let _guard = runtime_release_env_test_guard()
            .lock()
            .expect("lock release env test guard");
        let profile = load_bundled_release_profile().expect("load bundled release profile");
        assert!(!profile.environment.is_empty());
        assert!(!profile.control_plane_base_url.is_empty());
    }

    #[test]
    fn respects_local_override_when_profile_allows_it() {
        let _guard = runtime_release_env_test_guard()
            .lock()
            .expect("lock release env test guard");
        unsafe {
            env::set_var(CONTROL_PLANE_BASE_URL_ENV, " https://override.store.local/ ");
        }

        let resolved = resolve_release_profile().expect("resolve release profile");
        assert_eq!(
            resolved.profile.control_plane_base_url,
            "https://override.store.local"
        );

        unsafe {
            env::remove_var(CONTROL_PLANE_BASE_URL_ENV);
        }
    }
}
