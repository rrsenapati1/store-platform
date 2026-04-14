use crate::runtime_release::{resolve_release_profile, StoreRuntimeReleaseProfile};
use reqwest::Url;
use serde::{Deserialize, Serialize};
use tauri::AppHandle;
use tauri_plugin_updater::UpdaterExt;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeUpdateCheckResult {
    pub state: String,
    pub current_version: String,
    pub release_environment: String,
    pub updater_endpoint: Option<String>,
    pub update_version: Option<String>,
    pub notes: Option<String>,
    pub pub_date: Option<String>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeUpdateInstallResult {
    pub state: String,
    pub current_version: String,
    pub release_environment: String,
    pub updater_endpoint: Option<String>,
    pub installed_version: Option<String>,
    pub error: Option<String>,
}

fn unconfigured_check_result(
    current_version: String,
    profile: &StoreRuntimeReleaseProfile,
    error: &str,
) -> StoreRuntimeUpdateCheckResult {
    StoreRuntimeUpdateCheckResult {
        state: "unconfigured".to_string(),
        current_version,
        release_environment: profile.environment.clone(),
        updater_endpoint: profile.updater_endpoint.clone(),
        update_version: None,
        notes: None,
        pub_date: None,
        error: Some(error.to_string()),
    }
}

fn unconfigured_install_result(
    current_version: String,
    profile: &StoreRuntimeReleaseProfile,
    error: &str,
) -> StoreRuntimeUpdateInstallResult {
    StoreRuntimeUpdateInstallResult {
        state: "unconfigured".to_string(),
        current_version,
        release_environment: profile.environment.clone(),
        updater_endpoint: profile.updater_endpoint.clone(),
        installed_version: None,
        error: Some(error.to_string()),
    }
}

fn resolve_update_configuration(
    profile: &StoreRuntimeReleaseProfile,
) -> Result<(String, String), &'static str> {
    let endpoint = profile
        .updater_endpoint
        .clone()
        .ok_or("Updater endpoint is not configured for this release profile.")?;
    let pubkey = profile
        .updater_pubkey
        .clone()
        .ok_or("Updater public key is not configured for this release profile.")?;
    Ok((endpoint, pubkey))
}

#[tauri::command]
pub async fn cmd_check_store_runtime_update(
    app: AppHandle,
) -> Result<StoreRuntimeUpdateCheckResult, String> {
    let current_version = app.package_info().version.to_string();
    let resolved_profile = resolve_release_profile()?;
    let profile = resolved_profile.profile;
    let (endpoint, pubkey) = match resolve_update_configuration(&profile) {
        Ok(value) => value,
        Err(error) => {
            return Ok(unconfigured_check_result(current_version, &profile, error));
        }
    };

    let update = app
        .updater_builder()
        .endpoints(vec![Url::parse(&endpoint).map_err(|error| error.to_string())?])
        .map_err(|error| error.to_string())?
        .pubkey(pubkey)
        .build()
        .map_err(|error| error.to_string())?
        .check()
        .await
        .map_err(|error| error.to_string())?;

    if let Some(update) = update {
        return Ok(StoreRuntimeUpdateCheckResult {
            state: "update_available".to_string(),
            current_version,
            release_environment: profile.environment,
            updater_endpoint: Some(endpoint),
            update_version: Some(update.version.clone()),
            notes: update.body.clone(),
            pub_date: update.date.map(|date| date.to_string()),
            error: None,
        });
    }

    Ok(StoreRuntimeUpdateCheckResult {
        state: "up_to_date".to_string(),
        current_version,
        release_environment: profile.environment,
        updater_endpoint: Some(endpoint),
        update_version: None,
        notes: None,
        pub_date: None,
        error: None,
    })
}

#[tauri::command]
pub async fn cmd_install_store_runtime_update(
    app: AppHandle,
) -> Result<StoreRuntimeUpdateInstallResult, String> {
    let current_version = app.package_info().version.to_string();
    let resolved_profile = resolve_release_profile()?;
    let profile = resolved_profile.profile;
    let (endpoint, pubkey) = match resolve_update_configuration(&profile) {
        Ok(value) => value,
        Err(error) => {
            return Ok(unconfigured_install_result(current_version, &profile, error));
        }
    };

    let update = app
        .updater_builder()
        .endpoints(vec![Url::parse(&endpoint).map_err(|error| error.to_string())?])
        .map_err(|error| error.to_string())?
        .pubkey(pubkey)
        .build()
        .map_err(|error| error.to_string())?
        .check()
        .await
        .map_err(|error| error.to_string())?;

    let Some(update) = update else {
        return Ok(StoreRuntimeUpdateInstallResult {
            state: "up_to_date".to_string(),
            current_version,
            release_environment: profile.environment,
            updater_endpoint: Some(endpoint),
            installed_version: None,
            error: None,
        });
    };

    update
        .download_and_install(
            |_downloaded, _content_length| {},
            || {},
        )
        .await
        .map_err(|error| error.to_string())?;

    Ok(StoreRuntimeUpdateInstallResult {
        state: "installed".to_string(),
        current_version,
        release_environment: profile.environment,
        updater_endpoint: Some(endpoint),
        installed_version: Some(update.version),
        error: None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn requires_an_updater_endpoint() {
        let error = resolve_update_configuration(&StoreRuntimeReleaseProfile {
            environment: "staging".to_string(),
            control_plane_base_url: "https://control.acme.local".to_string(),
            updater_endpoint: None,
            updater_pubkey: Some("pubkey".to_string()),
            allow_local_control_plane_override: false,
            allow_downgrade_updates: false,
        })
        .expect_err("missing updater endpoint should fail");

        assert_eq!(
            error,
            "Updater endpoint is not configured for this release profile."
        );
    }

    #[test]
    fn requires_an_updater_pubkey() {
        let error = resolve_update_configuration(&StoreRuntimeReleaseProfile {
            environment: "staging".to_string(),
            control_plane_base_url: "https://control.acme.local".to_string(),
            updater_endpoint: Some("https://updates.acme.local/latest.json".to_string()),
            updater_pubkey: None,
            allow_local_control_plane_override: false,
            allow_downgrade_updates: false,
        })
        .expect_err("missing updater pubkey should fail");

        assert_eq!(
            error,
            "Updater public key is not configured for this release profile."
        );
    }
}
