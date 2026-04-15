use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

const CUSTOMER_DISPLAY_WINDOW_LABEL: &str = "store-customer-display";

fn customer_display_route() -> String {
    "index.html?customer-display=1".to_string()
}

#[tauri::command]
pub fn cmd_open_store_customer_display(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window(CUSTOMER_DISPLAY_WINDOW_LABEL) {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
        return Ok(());
    }

    WebviewWindowBuilder::new(
        &app,
        CUSTOMER_DISPLAY_WINDOW_LABEL,
        WebviewUrl::App(customer_display_route().into()),
    )
    .title("Store Customer Display")
    .inner_size(1280.0, 720.0)
    .decorations(false)
    .resizable(true)
    .build()
    .map_err(|error| error.to_string())?;

    Ok(())
}

#[tauri::command]
pub fn cmd_close_store_customer_display(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window(CUSTOMER_DISPLAY_WINDOW_LABEL) {
        window.close().map_err(|error| error.to_string())?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn customer_display_route_uses_the_query_marker() {
        assert_eq!(customer_display_route(), "index.html?customer-display=1");
    }

    #[test]
    fn customer_display_window_label_is_stable() {
        assert_eq!(CUSTOMER_DISPLAY_WINDOW_LABEL, "store-customer-display");
    }
}
