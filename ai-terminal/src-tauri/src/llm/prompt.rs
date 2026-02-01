use crate::context::TerminalContext;

/// Build the user prompt for completion request
pub fn build_user_prompt(ctx: &TerminalContext) -> String {
    crate::context::build_prompt(ctx)
}

/// Build the system prompt
pub fn build_system_prompt() -> String {
    crate::context::get_system_prompt().to_string()
}
