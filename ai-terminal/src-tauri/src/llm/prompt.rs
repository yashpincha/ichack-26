/// Build the system prompt
pub fn build_system_prompt() -> String {
    crate::context::get_system_prompt().to_string()
}
