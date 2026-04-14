use std::{env, fs, path::PathBuf};

const RELEASE_PROFILE_ENV: &str = "STORE_DESKTOP_RELEASE_PROFILE";
const RELEASE_CONTROL_PLANE_URL_ENV: &str = "STORE_DESKTOP_RELEASE_CONTROL_PLANE_BASE_URL";
const RELEASE_UPDATER_ENDPOINT_ENV: &str = "STORE_DESKTOP_RELEASE_UPDATER_ENDPOINT";
const RELEASE_UPDATER_PUBKEY_ENV: &str = "STORE_DESKTOP_RELEASE_UPDATER_PUBLIC_KEY";

fn main() {
    println!("cargo:rerun-if-env-changed={RELEASE_PROFILE_ENV}");
    println!("cargo:rerun-if-env-changed={RELEASE_CONTROL_PLANE_URL_ENV}");
    println!("cargo:rerun-if-env-changed={RELEASE_UPDATER_ENDPOINT_ENV}");
    println!("cargo:rerun-if-env-changed={RELEASE_UPDATER_PUBKEY_ENV}");
    println!("cargo:rerun-if-changed=release-profiles/dev.json");
    println!("cargo:rerun-if-changed=release-profiles/staging.json");
    println!("cargo:rerun-if-changed=release-profiles/prod.json");

    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("missing CARGO_MANIFEST_DIR"));
    let profile_name = env::var(RELEASE_PROFILE_ENV).unwrap_or_else(|_| "dev".to_string());
    let profile_path = manifest_dir.join("release-profiles").join(format!("{profile_name}.json"));
    let profile_raw = fs::read_to_string(&profile_path)
        .unwrap_or_else(|error| panic!("failed to load release profile {}: {}", profile_path.display(), error));
    let mut profile_json = serde_json::from_str::<serde_json::Value>(&profile_raw)
        .unwrap_or_else(|error| panic!("invalid release profile {}: {}", profile_path.display(), error));
    let profile_object = profile_json
        .as_object_mut()
        .unwrap_or_else(|| panic!("release profile {} must be a JSON object", profile_path.display()));

    apply_optional_override(profile_object, "control_plane_base_url", RELEASE_CONTROL_PLANE_URL_ENV);
    apply_optional_override(profile_object, "updater_endpoint", RELEASE_UPDATER_ENDPOINT_ENV);
    apply_optional_override(profile_object, "updater_pubkey", RELEASE_UPDATER_PUBKEY_ENV);

    let generated_json = serde_json::to_string(profile_object).expect("serialize release profile");
    let out_dir = PathBuf::from(env::var("OUT_DIR").expect("missing OUT_DIR"));
    let generated_path = out_dir.join("runtime_release_profile.rs");
    fs::write(
        generated_path,
        format!(
            "pub const BUNDLED_RELEASE_PROFILE_JSON: &str = {};\n",
            format!("{generated_json:?}")
        ),
    )
    .expect("write generated release profile");

    tauri_build::build()
}

fn apply_optional_override(
    target: &mut serde_json::Map<String, serde_json::Value>,
    key: &str,
    env_key: &str,
) {
    if let Ok(value) = env::var(env_key) {
        let normalized = value.trim();
        if !normalized.is_empty() {
            target.insert(key.to_string(), serde_json::Value::String(normalized.to_string()));
        }
    }
}
