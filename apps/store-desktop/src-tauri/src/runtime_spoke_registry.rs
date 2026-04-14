use serde::Serialize;
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct PendingSpokeActivation {
    pub activation_code: String,
    pub pairing_mode: String,
    pub runtime_profile: String,
    pub expires_at: String,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RegisteredSpokeSession {
    pub spoke_device_id: String,
    pub installation_id: String,
    pub runtime_kind: String,
    pub runtime_profile: String,
    pub hostname: Option<String>,
    pub app_version: Option<String>,
    pub spoke_runtime_token: String,
    pub expires_at: String,
    pub connection_state: String,
    pub last_seen_at: String,
}

#[derive(Debug, Default)]
pub struct RuntimeSpokeRegistry {
    pending_activations: HashMap<String, PendingSpokeActivation>,
    sessions_by_token: HashMap<String, RegisteredSpokeSession>,
    session_tokens_by_installation_id: HashMap<String, String>,
}

impl RuntimeSpokeRegistry {
    pub fn stage_activation(
        &mut self,
        activation_code: String,
        pairing_mode: String,
        runtime_profile: String,
        expires_at: String,
    ) -> PendingSpokeActivation {
        let activation = PendingSpokeActivation {
            activation_code: activation_code.clone(),
            pairing_mode,
            runtime_profile,
            expires_at,
        };
        self.pending_activations
            .insert(normalize_activation_code(&activation_code), activation.clone());
        activation
    }

    pub fn register_spoke(
        &mut self,
        activation_code: &str,
        installation_id: &str,
        runtime_kind: &str,
        runtime_profile: &str,
        hostname: Option<String>,
        app_version: Option<String>,
    ) -> Result<RegisteredSpokeSession, &'static str> {
        let Some(activation) = self
            .pending_activations
            .remove(&normalize_activation_code(activation_code))
        else {
            return Err("invalid_activation_code");
        };
        if activation.runtime_profile != runtime_profile {
            return Err("runtime_profile_mismatch");
        }

        let spoke_runtime_token = format!("srt_{}", Uuid::new_v4().simple());
        let session = RegisteredSpokeSession {
            spoke_device_id: build_spoke_device_id(installation_id),
            installation_id: installation_id.to_string(),
            runtime_kind: runtime_kind.to_string(),
            runtime_profile: runtime_profile.to_string(),
            hostname,
            app_version,
            spoke_runtime_token: spoke_runtime_token.clone(),
            expires_at: activation.expires_at,
            connection_state: "REGISTERED".to_string(),
            last_seen_at: now_hint(),
        };

        if let Some(existing_token) = self
            .session_tokens_by_installation_id
            .insert(session.installation_id.clone(), spoke_runtime_token.clone())
        {
            self.sessions_by_token.remove(&existing_token);
        }
        self.sessions_by_token
            .insert(spoke_runtime_token, session.clone());
        Ok(session)
    }

    pub fn heartbeat(&mut self, spoke_runtime_token: &str) -> Result<RegisteredSpokeSession, &'static str> {
        let Some(session) = self.sessions_by_token.get_mut(spoke_runtime_token) else {
            return Err("invalid_spoke_runtime_token");
        };
        session.connection_state = "CONNECTED".to_string();
        session.last_seen_at = now_hint();
        Ok(session.clone())
    }

    pub fn disconnect(&mut self, spoke_runtime_token: &str) -> Result<RegisteredSpokeSession, &'static str> {
        let Some(session) = self.sessions_by_token.get_mut(spoke_runtime_token) else {
            return Err("invalid_spoke_runtime_token");
        };
        session.connection_state = "DISCONNECTED".to_string();
        session.last_seen_at = now_hint();
        Ok(session.clone())
    }

    pub fn session_for_token(&self, spoke_runtime_token: &str) -> Option<RegisteredSpokeSession> {
        self.sessions_by_token.get(spoke_runtime_token).cloned()
    }

    pub fn connected_spoke_count(&self) -> usize {
        self.sessions_by_token
            .values()
            .filter(|session| session.connection_state == "CONNECTED")
            .count()
    }

    pub fn registered_spoke_count(&self) -> usize {
        self.sessions_by_token
            .values()
            .filter(|session| session.connection_state != "DISCONNECTED")
            .count()
    }
}

fn normalize_activation_code(code: &str) -> String {
    code.chars()
        .filter(|character| character.is_ascii_alphanumeric())
        .collect::<String>()
        .to_uppercase()
}

fn build_spoke_device_id(installation_id: &str) -> String {
    let normalized = installation_id
        .chars()
        .filter(|character| character.is_ascii_alphanumeric())
        .collect::<String>()
        .to_lowercase();
    let suffix = if normalized.len() > 12 {
        &normalized[normalized.len() - 12..]
    } else if normalized.is_empty() {
        "unknownspoke"
    } else {
        &normalized
    };
    format!("spoke-{suffix}")
}

fn now_hint() -> String {
    let seconds = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or_default();
    format!("{seconds}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn runtime_spoke_registry_stages_and_registers_spokes() {
        let mut registry = RuntimeSpokeRegistry::default();
        registry.stage_activation(
            "ACTV-ABCD-1234".to_string(),
            "qr".to_string(),
            "desktop_spoke".to_string(),
            "2099-01-01T00:00:00Z".to_string(),
        );

        let session = registry
            .register_spoke(
                "ACTV-ABCD-1234",
                "store-runtime-spoke-1",
                "packaged_desktop",
                "desktop_spoke",
                Some("COUNTER-02".to_string()),
                Some("0.1.0".to_string()),
            )
            .expect("register spoke");

        assert_eq!(session.connection_state, "REGISTERED");
        assert!(session.spoke_runtime_token.starts_with("srt_"));
    }
}
