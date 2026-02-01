#!/bin/bash
# Autocomplete.sh - LLM Powered Bash Completion
# MIT License - ClosedLoop Technologies, Inc.
# Sean Kruzel 2024-2025
#
# This script provides bash completion suggestions using an LLM.
# It includes enhanced error handling, refined sanitization, improved configuration parsing,
# streamlined provider-specific payload building, stronger caching eviction, and an updated interactive UX.
#
# Note: Do not enable “set -euo pipefail” here because it may interfere with bash completion.

###############################################################################
#                         Enhanced Error Handling                             #
###############################################################################

error_exit() {
    echo -e "\e[31mAutocomplete.sh - $1\e[0m" >&2
    # In a completion context, exit is too severe. Use return instead.
    return 1
}

echo_error() {
    echo -e "\e[31mAutocomplete.sh - $1\e[0m" >&2
}

echo_green() {
    echo -e "\e[32m$1\e[0m"
}

###############################################################################
#                      Global Variables & Model Definitions                   #
###############################################################################

export ACSH_VERSION=0.5.0

unset _autocomplete_modellist
declare -A _autocomplete_modellist
# OpenAI models
_autocomplete_modellist['openai:	gpt-4o']='{ "completion_cost":0.0000100, "prompt_cost":0.00000250, "endpoint": "https://api.openai.com/v1/chat/completions", "model": "gpt-4o", "provider": "openai" }'
_autocomplete_modellist['openai:	gpt-4o-mini']='{ "completion_cost":0.0000060, "prompt_cost":0.00000015, "endpoint": "https://api.openai.com/v1/chat/completions", "model": "gpt-4o-mini", "provider": "openai" }'
_autocomplete_modellist['openai:	o1']='{ "completion_cost":0.0000600, "prompt_cost":0.00001500, "endpoint": "https://api.openai.com/v1/chat/completions", "model": "o1", "provider": "openai" }'
_autocomplete_modellist['openai:	o1-mini']='{ "completion_cost":0.0000440, "prompt_cost":0.00001100, "endpoint": "https://api.openai.com/v1/chat/completions", "model": "o1-mini", "provider": "openai" }'
_autocomplete_modellist['openai:	o3-mini']='{ "completion_cost":0.0000440, "prompt_cost":0.00001100, "endpoint": "https://api.openai.com/v1/chat/completions", "model": "o3-mini", "provider": "openai" }'
# Anthropic models
_autocomplete_modellist['anthropic:	claude-3-7-sonnet-20250219']='{ "completion_cost":0.0000150, "prompt_cost":0.0000030, "endpoint": "https://api.anthropic.com/v1/messages", "model": "claude-3-7-sonnet-20240219", "provider": "anthropic" }'
_autocomplete_modellist['anthropic:	claude-3-5-sonnet-20241022']='{ "completion_cost":0.0000150, "prompt_cost":0.0000030, "endpoint": "https://api.anthropic.com/v1/messages", "model": "claude-3-5-sonnet-20241022", "provider": "anthropic" }'
_autocomplete_modellist['anthropic:	claude-3-5-haiku-20241022']='{ "completion_cost":0.0000040, "prompt_cost":0.0000008, "endpoint": "https://api.anthropic.com/v1/messages", "model": "claude-3-5-haiku-20241022", "provider": "anthropic" }'
# Groq models
_autocomplete_modellist['groq:		llama3-8b-8192']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "llama3-8b-8192", "provider": "groq" }'
_autocomplete_modellist['groq:		llama3-70b-8192']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "llama3-70b-8192", "provider": "groq" }'
_autocomplete_modellist['groq:		llama-3.3-70b-versatile']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "llama-3.3-70b-versatile", "provider": "groq" }'
_autocomplete_modellist['groq:		llama-3.1-8b-instant']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "llama-3.1-8b-instant", "provider": "groq" }'
_autocomplete_modellist['groq:		llama-guard-3-8b']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "llama-guard-3-8b", "provider": "groq" }'
_autocomplete_modellist['groq:		mixtral-8x7b-32768']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "mixtral-8x7b-32768", "provider": "groq" }'
_autocomplete_modellist['groq:		gemma2-9b-it']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "gemma2-9b-it", "provider": "groq" }'
# Groq preview models
_autocomplete_modellist['groq:		mistral-saba-24b']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "mistral-saba-24b", "provider": "groq" }'
_autocomplete_modellist['groq:		qwen-2.5-coder-32b']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "qwen-2.5-coder-32b", "provider": "groq" }'
_autocomplete_modellist['groq:		deepseek-r1-distill-qwen-32b']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "deepseek-r1-distill-qwen-32b", "provider": "groq" }'
_autocomplete_modellist['groq:		deepseek-r1-distill-llama-70b-specdec']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "deepseek-r1-distill-llama-70b-specdec", "provider": "groq" }'
_autocomplete_modellist['groq:		llama-3.3-70b-specdec']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "llama-3.3-70b-specdec", "provider": "groq" }'
_autocomplete_modellist['groq:		llama-3.2-1b-preview']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "llama-3.2-1b-preview", "provider": "groq" }'
_autocomplete_modellist['groq:		llama-3.2-3b-preview']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "llama-3.2-3b-preview", "provider": "groq" }'
# Ollama models
_autocomplete_modellist['ollama:	codellama']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "http://localhost:11434/api/chat", "model": "codellama", "provider": "ollama" }'
_autocomplete_modellist['ollama:	qwen2.5-coder:7b-instruct']='{ "completion_cost":0.0000000, "prompt_cost":0.0000000, "endpoint": "http://localhost:11434/api/chat", "model": "qwen2.5-coder:7b-instruct", "provider": "ollama" }'

###############################################################################
#                    Load .env from script directory (for API key)            #
###############################################################################
_acsh_load_dotenv() {
    local script_dir script_src
    script_src="${BASH_SOURCE[0]:-$0}"
    if [[ "$script_src" != /* ]]; then
        script_src="$(command -v "$script_src" 2>/dev/null || echo "$script_src")"
    fi
    if [[ -n "$script_src" ]]; then
        script_dir="$(cd "$(dirname "$(readlink -f "$script_src" 2>/dev/null || echo "$script_src")")" && pwd)" 2>/dev/null || true
    fi
    if [[ -z "$script_dir" ]]; then
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
    fi
    if [[ -n "$script_dir" && -f "$script_dir/.env" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "$script_dir/.env"
        set +a
    fi
    if [[ -f "$HOME/.autocomplete/.env" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "$HOME/.autocomplete/.env"
        set +a
    fi
}
_acsh_load_dotenv

###############################################################################
#                    FEP (Fix Error Please) - Context Capture                  #
###############################################################################
# Only set defaults if not already set (so "ACSH_LAST_COMMAND=cmd autocomplete fep" works)
export ACSH_LAST_COMMAND="${ACSH_LAST_COMMAND:-}"
export ACSH_LAST_EXIT_CODE="${ACSH_LAST_EXIT_CODE:-}"
export ACSH_LAST_OUTPUT_FILE="${ACSH_LAST_OUTPUT_FILE:-$HOME/.autocomplete/last_output.txt}"

_acsh_capture_command_result() {
    export ACSH_LAST_EXIT_CODE="$?"
    export ACSH_LAST_COMMAND="$(fc -ln -1 2>/dev/null | sed 's/^[[:space:]]*//')"
}

###############################################################################
#                       System Information Functions                          #
###############################################################################

_get_terminal_info() {
    local terminal_info=" * User name: \$USER=$USER
 * Current directory: \$PWD=$PWD
 * Previous directory: \$OLDPWD=$OLDPWD
 * Home directory: \$HOME=$HOME
 * Operating system: \$OSTYPE=$OSTYPE
 * Shell: \$BASH=$BASH
 * Terminal type: \$TERM=$TERM
 * Hostname: \$HOSTNAME"
    echo "$terminal_info"
}

machine_signature() {
    local signature
    signature=$(echo "$(uname -a)|$$USER" | md5sum | cut -d ' ' -f 1)
    echo "$signature"
}

_system_info() {
    echo "# System Information"
    echo
    uname -a
    echo "SIGNATURE: $(machine_signature)"
    echo
    echo "BASH_VERSION: $BASH_VERSION"
    echo "BASH_COMPLETION_VERSINFO: ${BASH_COMPLETION_VERSINFO}"
    echo
    echo "## Terminal Information"
    _get_terminal_info
}

_completion_vars() {
    echo "BASH_COMPLETION_VERSINFO: ${BASH_COMPLETION_VERSINFO}"
    echo "COMP_CWORD: ${COMP_CWORD}"
    echo "COMP_KEY: ${COMP_KEY}"
    echo "COMP_LINE: ${COMP_LINE}"
    echo "COMP_POINT: ${COMP_POINT}"
    echo "COMP_TYPE: ${COMP_TYPE}"
    echo "COMP_WORDBREAKS: ${COMP_WORDBREAKS}"
    echo "COMP_WORDS: ${COMP_WORDS[*]}"
}

###############################################################################
#                      LLM Completion Functions                               #
###############################################################################

_get_system_message_prompt() {
    echo "You are a helpful bash_completion script. Generate relevant and concise auto-complete suggestions for the given user command in the context of the current directory, operating system, command history, and environment variables. For each suggestion, provide both the command and a brief one-line explanation of what it does. The output must be a list of two to five possible completions or rewritten commands. Each must be a valid command or chain of commands. Do not include backticks or quotes in the commands."
}

_get_output_instructions() {
    echo "Provide a list of suggested completions or commands that could be run in the terminal. YOU MUST provide a list of two to five possible completions or rewritten commands. For each command, include a brief one-line explanation (max 60 characters) of what it does. DO NOT wrap the commands in backticks or quotes. Each must be a valid command or chain of commands. Focus on the user's intent, recent commands, and the current environment. RETURN A JSON OBJECT WITH THE COMPLETIONS AND THEIR EXPLANATIONS."
}

_get_command_history() {
    local HISTORY_LIMIT=${ACSH_MAX_HISTORY_COMMANDS:-20}
    history | tail -n "$HISTORY_LIMIT"
}

# Refined sanitization: only replace long hex sequences, UUIDs, and API-key–like tokens.
_get_clean_command_history() {
    local recent_history
    recent_history=$(_get_command_history)
    recent_history=$(echo "$recent_history" | sed -E 's/\b[[:xdigit:]]{32,40}\b/REDACTED_HASH/g')
    recent_history=$(echo "$recent_history" | sed -E 's/\b[0-9a-fA-F-]{36}\b/REDACTED_UUID/g')
    recent_history=$(echo "$recent_history" | sed -E 's/\b[A-Za-z0-9]{16,40}\b/REDACTED_APIKEY/g')
    echo "$recent_history"
}

_get_recent_files() {
    local FILE_LIMIT=${ACSH_MAX_RECENT_FILES:-20}
    find . -maxdepth 1 -type f -exec ls -ld {} + | sort -r | head -n "$FILE_LIMIT"
}

# Rewritten _get_help_message using a heredoc to preserve formatting.
_get_help_message() {
    local COMMAND HELP_INFO
    COMMAND=$(echo "$1" | awk '{print $1}')
    HELP_INFO=""
    {
        set +e
        HELP_INFO=$(cat <<EOF
$($COMMAND --help 2>&1 || true)
EOF
        )
        set -e
    } || HELP_INFO="'$COMMAND --help' not available"
    echo "$HELP_INFO"
}

_build_prompt() {
    local user_input command_history terminal_context help_message recent_files output_instructions other_environment_variables prompt
    user_input="$*"
    command_history=$(_get_clean_command_history)
    terminal_context=$(_get_terminal_info)
    help_message=$(_get_help_message "$user_input")
    recent_files=$(_get_recent_files)
    output_instructions=$(_get_output_instructions)
    other_environment_variables=$(env | grep '=' | grep -v 'ACSH_' | awk -F= '{print $1}' | grep -v 'PWD\|OSTYPE\|BASH\|USER\|HOME\|TERM\|OLDPWD\|HOSTNAME')
    
    prompt="User command: \`$user_input\`

# Terminal Context
## Environment variables
$terminal_context

Other defined environment variables
\`\`\`
$other_environment_variables
\`\`\`

## History
Recently run commands (some information redacted):
\`\`\`
$command_history
\`\`\`

## File system
Most recently modified files:
\`\`\`
$recent_files
\`\`\`

## Help Information
$help_message

# Instructions
$output_instructions
"
    echo "$prompt"
}

_build_fep_prompt() {
    local user_context="$1"
    local last_cmd="${ACSH_LAST_COMMAND:-$(fc -ln -1 2>/dev/null | sed 's/^[[:space:]]*//')}"
    local last_exit="${ACSH_LAST_EXIT_CODE:-$?}"
    local last_output=""

    [[ -f "$ACSH_LAST_OUTPUT_FILE" ]] && last_output="$(tail -100 "$ACSH_LAST_OUTPUT_FILE")"

    cat <<EOF
# Error Recovery Request

## Failed Command
\`\`\`bash
$last_cmd
\`\`\`

## Exit Code
$last_exit

## Command Output/Error
\`\`\`
${last_output:-"(No captured output - please describe the error)"}
\`\`\`

## Additional Context from User
${user_context:-"(None provided)"}

## Environment
$(printf "%s\n" "$(_get_terminal_info)")

## Current Directory Contents
$(ls -la 2>/dev/null | head -20)

## Recent Command History
$(fc -ln -10 2>/dev/null)

# Instructions
Analyze the failed command and error. Provide:
1. **Recommended Command**: A corrected or alternative command that fixes the issue
2. **Explanation**: Brief explanation of what went wrong and why the fix works

Respond in this exact JSON format:
{
    "recommended_command": "the fixed command here",
    "explanation": "brief explanation of the fix"
}
EOF
}

###############################################################################
#                      Payload Building Functions                             #
###############################################################################

build_common_payload() {
    jq -n --arg model "$model" \
          --arg temperature "$temperature" \
          --arg system_prompt "$system_prompt" \
          --arg prompt_content "$prompt_content" \
          '{
             model: $model,
             messages: [
               {role: "system", content: $system_prompt},
               {role: "user", content: $prompt_content}
             ],
             temperature: ($temperature | tonumber)
          }'
}

_build_payload() {
    local user_input prompt system_message_prompt payload acsh_prompt
    local model temperature
    model="${ACSH_MODEL:-gpt-4o}"
    temperature="${ACSH_TEMPERATURE:-0.0}"

    user_input="$1"
    prompt=$(_build_prompt "$@")
    system_message_prompt=$(_get_system_message_prompt)

    acsh_prompt="# SYSTEM PROMPT
$system_message_prompt
# USER MESSAGE
$prompt"
    export ACSH_PROMPT="$acsh_prompt"

    prompt_content="$prompt"
    system_prompt="$system_message_prompt"

    local base_payload
    base_payload=$(build_common_payload)

    case "${ACSH_PROVIDER^^}" in
        "ANTHROPIC")
            payload=$(echo "$base_payload" | jq '. + {
                system: .messages[0].content,
                messages: [{role:"user", content: .messages[1].content}],
                max_tokens: 1024,
                tool_choice: {type: "tool", name: "bash_completions"},
                tools: [{
                    name: "bash_completions",
                    description: "syntactically correct command-line suggestions with explanations",
                    input_schema: {
                        type: "object",
                        properties: {
                            suggestions: {
                                type: "array",
                                items: {
                                    type: "object",
                                    properties: {
                                        command: {type: "string", description: "The suggested command"},
                                        explanation: {type: "string", description: "Brief explanation of what the command does"}
                                    },
                                    required: ["command", "explanation"]
                                }
                            }
                        },
                        required: ["suggestions"]
                    }
                }]
            }')
            ;;
        "GROQ")
            payload=$(echo "$base_payload" | jq '. + {response_format: {type: "json_object"}}')
            ;;
        "OLLAMA")
            payload=$(echo "$base_payload" | jq '. + {
                format: "json",
                stream: false,
                options: {temperature: (.temperature | tonumber)}
            }')
            ;;
        *)
            payload=$(echo "$base_payload" | jq '. + {
                response_format: {type: "json_object"},
                tool_choice: {
                    type: "function",
                    function: {
                        name: "bash_completions",
                        description: "syntactically correct command-line suggestions with explanations",
                        parameters: {
                            type: "object",
                            properties: {
                                suggestions: {
                                    type: "array",
                                    items: {
                                        type: "object",
                                        properties: {
                                            command: {type: "string", description: "The suggested command"},
                                            explanation: {type: "string", description: "Brief explanation of what the command does"}
                                        },
                                        required: ["command", "explanation"]
                                    }
                                }
                            },
                            required: ["suggestions"]
                        }
                    }
                },
                tools: [{
                    type: "function",
                    function: {
                        name: "bash_completions",
                        description: "syntactically correct command-line suggestions with explanations",
                        parameters: {
                            type: "object",
                            properties: {
                                suggestions: {
                                    type: "array",
                                    items: {
                                        type: "object",
                                        properties: {
                                            command: {type: "string", description: "The suggested command"},
                                            explanation: {type: "string", description: "Brief explanation of what the command does"}
                                        },
                                        required: ["command", "explanation"]
                                    }
                                }
                            },
                            required: ["suggestions"]
                        }
                    }
                }]
            }')
            ;;
    esac
    echo "$payload"
}

log_request() {
    local user_input response_body user_input_hash log_file prompt_tokens completion_tokens created api_cost
    local prompt_tokens_int completion_tokens_int
    user_input="$1"
    response_body="$2"
    user_input_hash=$(echo -n "$user_input" | md5sum | cut -d ' ' -f 1)

    if [[ "${ACSH_PROVIDER^^}" == "ANTHROPIC" ]]; then
        prompt_tokens=$(echo "$response_body" | jq -r '.usage.input_tokens')
        prompt_tokens_int=$((prompt_tokens))
        completion_tokens=$(echo "$response_body" | jq -r '.usage.output_tokens')
        completion_tokens_int=$((completion_tokens))
    else
        prompt_tokens=$(echo "$response_body" | jq -r '.usage.prompt_tokens')
        prompt_tokens_int=$((prompt_tokens))
        completion_tokens=$(echo "$response_body" | jq -r '.usage.completion_tokens')
        completion_tokens_int=$((completion_tokens))
    fi

    created=$(date +%s)
    created=$(echo "$response_body" | jq -r ".created // $created")
    api_cost=$(echo "$prompt_tokens_int * $ACSH_API_PROMPT_COST + $completion_tokens_int * $ACSH_API_COMPLETION_COST" | bc)
    log_file=${ACSH_LOG_FILE:-"$HOME/.autocomplete/autocomplete.log"}
    echo "$created,$user_input_hash,$prompt_tokens_int,$completion_tokens_int,$api_cost" >> "$log_file"
}

openai_completion() {
    local content status_code response_body default_user_input user_input api_key payload endpoint timeout attempt max_attempts
    endpoint=${ACSH_ENDPOINT:-"https://api.openai.com/v1/chat/completions"}
    timeout=${ACSH_TIMEOUT:-30}
    default_user_input="Write two to six most likely commands given the provided information"
    user_input=${*:-$default_user_input}

    if [[ -z "$ACSH_ACTIVE_API_KEY" && ${ACSH_PROVIDER^^} != "OLLAMA" ]]; then
        echo_error "ACSH_ACTIVE_API_KEY not set. Please set it with: export ${ACSH_PROVIDER^^}_API_KEY=<your-api-key>"
        return
    fi
    api_key="${ACSH_ACTIVE_API_KEY:-$OPENAI_API_KEY}"
    payload=$(_build_payload "$user_input")
    
    max_attempts=2
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        # Use 'command' to bypass wrapper functions and prevent infinite recursion
        if [[ "${ACSH_PROVIDER^^}" == "ANTHROPIC" ]]; then
            response=$(command curl -s -m "$timeout" -w "\n%{http_code}" "$endpoint" \
                -H "content-type: application/json" \
                -H "anthropic-version: 2023-06-01" \
                -H "x-api-key: $api_key" \
                --data "$payload")
        elif [[ "${ACSH_PROVIDER^^}" == "OLLAMA" ]]; then
            response=$(command curl -s -m "$timeout" -w "\n%{http_code}" "$endpoint" --data "$payload")
        else
            response=$(command curl -s -m "$timeout" -w "\n%{http_code}" "$endpoint" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $api_key" \
                -d "$payload")
        fi
        status_code=$(echo "$response" | tail -n1)
        response_body=$(echo "$response" | sed '$d')
        if [[ $status_code -eq 200 ]]; then
            break
        else
            echo_error "API call failed with status $status_code. Retrying... (Attempt $attempt of $max_attempts)"
            sleep 1
            attempt=$((attempt+1))
        fi
    done

    if [[ $status_code -ne 200 ]]; then
        case $status_code in
            400) echo_error "Bad Request: The API request was invalid or malformed." ;;
            401) echo_error "Unauthorized: The provided API key is invalid or missing." ;;
            429) echo_error "Too Many Requests: The API rate limit has been exceeded." ;;
            500) echo_error "Internal Server Error: An unexpected error occurred on the API server." ;;
            *) echo_error "Unknown Error: Unexpected status code $status_code received. Response: $response_body" ;;
        esac
        return
    fi

    if [[ "${ACSH_PROVIDER^^}" == "ANTHROPIC" ]]; then
        content=$(echo "$response_body" | jq -r '.content[0].input.suggestions')
    elif [[ "${ACSH_PROVIDER^^}" == "GROQ" ]]; then
        content=$(echo "$response_body" | jq -r '.choices[0].message.content')
        content=$(echo "$content" | jq -r '.suggestions // .completions')
    elif [[ "${ACSH_PROVIDER^^}" == "OLLAMA" ]]; then
        content=$(echo "$response_body" | jq -r '.message.content')
        content=$(echo "$content" | jq -r '.suggestions // .completions')
    else
        content=$(echo "$response_body" | jq -r '.choices[0].message.tool_calls[0].function.arguments')
        content=$(echo "$content" | jq -r '.suggestions // .commands')
    fi

    local completions
    # Format: "command|||explanation" for each line
    if echo "$content" | jq -e 'type == "array"' &>/dev/null; then
        # New format with suggestions array
        completions=$(echo "$content" | jq -r '.[] | .command + "|||" + .explanation' | grep -v '^$')
    else
        # Fallback for old format (just commands)
        completions=$(echo "$content" | jq -r '.[]' | grep -v '^$' | sed 's/$/|||/')
    fi
    echo -n "$completions"
    log_request "$user_input" "$response_body"
}

_build_fep_payload() {
    local prompt="$1"
    local model temperature
    model="${ACSH_MODEL:-gpt-4o}"
    temperature="${ACSH_TEMPERATURE:-0.0}"
    local system_prompt="You are an expert command-line debugger. Analyze errors and provide fixes. Respond only with valid JSON in this exact format: {\"recommended_command\": \"the fixed command\", \"explanation\": \"brief explanation\"}."
    local base_payload
    base_payload=$(jq -n --arg model "$model" \
        --arg temperature "$temperature" \
        --arg system_prompt "$system_prompt" \
        --arg prompt "$prompt" \
        '{
            model: $model,
            messages: [
                {role: "system", content: $system_prompt},
                {role: "user", content: $prompt}
            ],
            temperature: ($temperature | tonumber)
        }')
    case "${ACSH_PROVIDER^^}" in
        "ANTHROPIC")
            echo "$base_payload" | jq '. + {max_tokens: 1024}'
            ;;
        "GROQ")
            echo "$base_payload" | jq '. + {response_format: {type: "json_object"}}'
            ;;
        "OLLAMA")
            echo "$base_payload" | jq '. + {format: "json", stream: false}'
            ;;
        *)
            echo "$base_payload" | jq '. + {response_format: {type: "json_object"}}'
            ;;
    esac
}

fep_completion() {
    local user_context="$1"
    local prompt endpoint payload response status_code response_body api_key timeout attempt max_attempts

    prompt="$(_build_fep_prompt "$user_context")"
    endpoint="${ACSH_ENDPOINT:-https://api.openai.com/v1/chat/completions}"
    timeout="${ACSH_TIMEOUT:-60}"
    api_key="${ACSH_ACTIVE_API_KEY:-$OPENAI_API_KEY}"

    if [[ -z "$api_key" && "${ACSH_PROVIDER^^}" != "OLLAMA" ]]; then
        echo_error "ACSH_ACTIVE_API_KEY not set. Run: autocomplete config (or set OPENAI_API_KEY)"
        return 1
    fi

    payload=$(_build_fep_payload "$prompt")
    max_attempts=2
    attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if [[ "${ACSH_PROVIDER^^}" == "ANTHROPIC" ]]; then
            response=$(curl -s -m "$timeout" -w "\n%{http_code}" "$endpoint" \
                -H "content-type: application/json" \
                -H "anthropic-version: 2023-06-01" \
                -H "x-api-key: $api_key" \
                --data "$payload")
        elif [[ "${ACSH_PROVIDER^^}" == "OLLAMA" ]]; then
            response=$(curl -s -m "$timeout" -w "\n%{http_code}" "$endpoint" --data "$payload")
        else
            response=$(curl -s -m "$timeout" -w "\n%{http_code}" "$endpoint" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $api_key" \
                -d "$payload")
        fi
        status_code=$(echo "$response" | tail -n1)
        response_body=$(echo "$response" | sed '$d')
        if [[ $status_code -eq 200 ]]; then
            break
        fi
        echo_error "API call failed with status $status_code. Retrying... (Attempt $attempt of $max_attempts)" >&2
        sleep 1
        attempt=$((attempt + 1))
    done

    if [[ $status_code -ne 200 ]]; then
        echo_error "FEP request failed. Status: $status_code"
        return 1
    fi

    # Echo full response so caller can parse .message.content or .choices[0].message.content
    echo "$response_body"
}

###############################################################################
#                        Harm Detection Functions                             #
###############################################################################

_build_harm_detection_payload() {
    local command="$1"
    local model temperature system_prompt prompt_content

    model="${ACSH_MODEL:-gpt-4o}"
    temperature="0.0"  # Use deterministic responses for safety checks

    system_prompt="You are a bash command security analyzer. Your role is to identify potentially harmful bash commands that could cause data loss, system damage, security risks, or unintended consequences. Analyze commands for: destructive file operations, system modifications, permission changes, network security risks, resource consumption attacks, and dangerous command chaining."

    prompt_content="Analyze this bash command for potential harm:

Command: $command

Classify this command and respond with ONLY a JSON object in this exact format:
{
  \"is_harmful\": true or false,
  \"explanation\": \"Brief explanation of why this command is harmful or safe (max 100 chars)\"
}"

    local base_payload
    base_payload=$(jq -n --arg model "$model" \
                         --arg temperature "$temperature" \
                         --arg system_prompt "$system_prompt" \
                         --arg prompt_content "$prompt_content" \
                         '{
                            model: $model,
                            messages: [
                              {role: "system", content: $system_prompt},
                              {role: "user", content: $prompt_content}
                            ],
                            temperature: ($temperature | tonumber)
                          }')

    local payload
    case "${ACSH_PROVIDER^^}" in
        "ANTHROPIC")
            payload=$(echo "$base_payload" | jq '. + {
                system: .messages[0].content,
                messages: [{role:"user", content: .messages[1].content}],
                max_tokens: 512,
                tool_choice: {type: "tool", name: "harm_assessment"},
                tools: [{
                    name: "harm_assessment",
                    description: "Assess if a bash command is potentially harmful",
                    input_schema: {
                        type: "object",
                        properties: {
                            is_harmful: {type: "boolean", description: "Whether the command is harmful"},
                            explanation: {type: "string", description: "Brief explanation of the assessment"}
                        },
                        required: ["is_harmful", "explanation"]
                    }
                }]
            }')
            ;;
        "GROQ")
            payload=$(echo "$base_payload" | jq '. + {response_format: {type: "json_object"}}')
            ;;
        "OLLAMA")
            payload=$(echo "$base_payload" | jq '. + {
                format: "json",
                stream: false,
                options: {temperature: 0.0}
            }')
            ;;
        *)
            # OpenAI default - use function calling
            payload=$(echo "$base_payload" | jq '. + {
                tools: [{
                    type: "function",
                    function: {
                        name: "harm_assessment",
                        description: "Assess if a bash command is potentially harmful",
                        parameters: {
                            type: "object",
                            properties: {
                                is_harmful: {type: "boolean", description: "Whether the command is harmful"},
                                explanation: {type: "string", description: "Brief explanation"}
                            },
                            required: ["is_harmful", "explanation"]
                        }
                    }
                }],
                tool_choice: {type: "function", function: {name: "harm_assessment"}}
            }')
            ;;
    esac
    echo "$payload"
}

detect_command_harm() {
    local command="$1"
    local command_hash cache_file cache_dir harm_response

    # Load configuration to ensure API keys are set
    acsh_load_config

    # Generate cache hash
    command_hash=$(echo -n "$command" | md5sum | cut -d ' ' -f 1)
    cache_dir="${ACSH_HARM_CACHE_DIR:-$HOME/.autocomplete/harm_cache}"
    cache_file="$cache_dir/harm-$command_hash.json"

    # Check cache first (instant return)
    if [[ -d "$cache_dir" && -f "$cache_file" ]]; then
        cat "$cache_file"
        return 0
    fi

    # Build and send API request
    local payload endpoint timeout api_key response status_code response_body

    endpoint=${ACSH_ENDPOINT:-"https://api.openai.com/v1/chat/completions"}
    timeout=${ACSH_HARM_TIMEOUT:-3}
    api_key="${ACSH_ACTIVE_API_KEY:-$OPENAI_API_KEY}"

    payload=$(_build_harm_detection_payload "$command")

    # Debug: notify that we're making an API request
    echo -e "\e[90m[DEBUG] Submitting API request to check command harm: $command\e[0m" >&2

    # Call API with short timeout for harm detection
    # Use 'command' to bypass wrapper functions and prevent infinite recursion
    if [[ "${ACSH_PROVIDER^^}" == "ANTHROPIC" ]]; then
        response=$(command curl -s -m "$timeout" -w "\n%{http_code}" "$endpoint" \
            -H "content-type: application/json" \
            -H "anthropic-version: 2023-06-01" \
            -H "x-api-key: $api_key" \
            --data "$payload")
    elif [[ "${ACSH_PROVIDER^^}" == "OLLAMA" ]]; then
        response=$(command curl -s -m "$timeout" -w "\n%{http_code}" "$endpoint" --data "$payload")
    else
        response=$(command curl -s -m "$timeout" -w "\n%{http_code}" "$endpoint" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $api_key" \
            -d "$payload")
    fi

    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')

    # Handle API failure - default to safe (fail open)
    if [[ $status_code -ne 200 ]]; then
        echo_error "Harm detection API call failed with status $status_code. Allowing command execution." >&2
        echo '{"is_harmful":false,"explanation":"API unavailable - defaulting to safe"}'
        return 0
    fi

    # Parse response based on provider
    local harm_data
    if [[ "${ACSH_PROVIDER^^}" == "ANTHROPIC" ]]; then
        harm_data=$(echo "$response_body" | jq -r '.content[0].input')
    elif [[ "${ACSH_PROVIDER^^}" == "GROQ" ]]; then
        harm_data=$(echo "$response_body" | jq -r '.choices[0].message.content')
    elif [[ "${ACSH_PROVIDER^^}" == "OLLAMA" ]]; then
        harm_data=$(echo "$response_body" | jq -r '.message.content')
    else
        # OpenAI function calling - arguments is a JSON string that needs parsing
        local arguments_string
        arguments_string=$(echo "$response_body" | jq -r '.choices[0].message.tool_calls[0].function.arguments // .choices[0].message.content')
        # Parse the JSON string to get the actual JSON object
        harm_data=$(echo "$arguments_string" | jq -c '.')
    fi

    # Validate JSON structure - if malformed, default to safe
    if ! echo "$harm_data" | jq -e 'has("is_harmful")' &>/dev/null; then
        echo_error "Malformed harm detection response. Allowing command execution." >&2
        echo '{"is_harmful":false,"explanation":"Malformed response - defaulting to safe"}'
        return 0
    fi

    # Cache the result
    mkdir -p "$cache_dir"
    echo "$harm_data" > "$cache_file"

    echo "$harm_data"
}

###############################################################################
#                        Completion Functions                                 #
###############################################################################

_get_default_completion_function() {
    local cmd="$1"
    complete -p "$cmd" 2>/dev/null | awk -F' ' '{ for(i=1;i<=NF;i++) { if ($i ~ /^-F$/) { print $(i+1); exit; } } }'
}

_default_completion() {
    local current_word="" first_word="" default_func
    if [[ -n "${COMP_WORDS[*]}" ]]; then
        first_word="${COMP_WORDS[0]}"
        if [[ -n "$COMP_CWORD" && "$COMP_CWORD" -lt "${#COMP_WORDS[@]}" ]]; then
            current_word="${COMP_WORDS[COMP_CWORD]}"
        fi
    fi

    default_func=$(_get_default_completion_function "$first_word")
    if [[ -n "$default_func" ]]; then
        "$default_func"
    else
        local file_completions
        if [[ -z "$current_word" ]]; then
            file_completions=$(compgen -f -- || true)
        else
            file_completions=$(compgen -f -- "$current_word" || true)
        fi
        if [[ -n "$file_completions" ]]; then
            readarray -t COMPREPLY <<<"$file_completions"
        fi
    fi
}

list_cache() {
    local cache_dir=${ACSH_CACHE_DIR:-"$HOME/.autocomplete/cache"}
    find "$cache_dir" -maxdepth 1 -type f -name "acsh-*" -printf '%T+ %p\n' | sort
}

_autocompletesh() {
    _init_completion || return
    _default_completion
    if [[ ${#COMPREPLY[@]} -eq 0 && $COMP_TYPE -eq 63 ]]; then
        local completions user_input user_input_hash
        acsh_load_config
        if [[ -z "$ACSH_ACTIVE_API_KEY" && ${ACSH_PROVIDER^^} != "OLLAMA" ]]; then
            local provider_key="${ACSH_PROVIDER:-openai}_API_KEY"
            provider_key=$(echo "$provider_key" | tr '[:lower:]' '[:upper:]')
            echo_error "${provider_key} is not set. Please set it using: export ${provider_key}=<your-api-key> or disable autocomplete via: autocomplete disable"
            echo
            return
        fi
        if [[ -n "${COMP_WORDS[*]}" ]]; then
            command="${COMP_WORDS[0]}"
            if [[ -n "$COMP_CWORD" && "$COMP_CWORD" -lt "${#COMP_WORDS[@]}" ]]; then
                current="${COMP_WORDS[COMP_CWORD]}"
            fi
        fi
        user_input="${COMP_LINE:-"$command $current"}"
        user_input_hash=$(echo -n "$user_input" | md5sum | cut -d ' ' -f 1)
        export ACSH_INPUT="$user_input"
        export ACSH_PROMPT=
        export ACSH_RESPONSE=
        local cache_dir=${ACSH_CACHE_DIR:-"$HOME/.autocomplete/cache"}
        local cache_size=${ACSH_CACHE_SIZE:-100}
        local cache_file="$cache_dir/acsh-$user_input_hash.txt"
        if [[ -d "$cache_dir" && "$cache_size" -gt 0 && -f "$cache_file" ]]; then
            completions=$(cat "$cache_file" || true)
            touch "$cache_file"
        else
            echo -en "\e]12;green\a"
            completions=$(openai_completion "$user_input" || true)
            if [[ -z "$completions" ]]; then
                echo -en "\e]12;red\a"
                sleep 1
                completions=$(openai_completion "$user_input" || true)
            fi
            echo -en "\e]12;white\a"
            if [[ -d "$cache_dir" && "$cache_size" -gt 0 ]]; then
                echo "$completions" > "$cache_file"
                while [[ $(list_cache | wc -l) -gt "$cache_size" ]]; do
                    oldest=$(list_cache | head -n 1 | cut -d ' ' -f 2-)
                    rm "$oldest" || true
                done
            fi
        fi
        export ACSH_RESPONSE=$completions

        # Store completions for interactive mode
        export ACSH_LAST_COMPLETIONS="$completions"

        if [[ -n "$completions" ]]; then
            local num_rows
            num_rows=$(echo "$completions" | wc -l)
            COMPREPLY=()
            # Extract just the command part (before |||) for display
            local cmd_only
            cmd_only=$(echo "$completions" | sed 's/|||.*//')
            if [[ $num_rows -eq 1 ]]; then
                readarray -t COMPREPLY <<<"$(echo -n "${cmd_only}" | sed "s/${command}[[:space:]]*//" | sed 's/:/\\:/g')"
            else
                cmd_only=$(echo "$cmd_only" | awk '{print NR". "$0}')
                readarray -t COMPREPLY <<< "$cmd_only"
            fi
        fi
        if [[ ${#COMPREPLY[@]} -eq 0 ]]; then
            COMPREPLY=("$current")
        fi
    fi
}

# Interactive autocomplete function that can be bound to a key
_interactive_autocomplete_widget() {
    local user_input completions show_explanations

    # Get current line content
    user_input="${READLINE_LINE}"

    # If line is empty, return
    if [[ -z "$user_input" ]]; then
        return
    fi

    # Check if user wants explanations
    show_explanations=false
    if [[ "$user_input" == *"--explain"* ]]; then
        show_explanations=true
        # Remove the "--explain" flag from the input before sending to API
        user_input="${user_input%%--explain*}"
        user_input="${user_input%% }"  # Trim trailing space
    fi

    # Load config
    acsh_load_config

    # Check API key
    if [[ -z "$ACSH_ACTIVE_API_KEY" && ${ACSH_PROVIDER^^} != "OLLAMA" ]]; then
        echo
        echo_error "API key not set. Configure with: autocomplete config"
        return
    fi

    # Get completions from cache or API
    local user_input_hash cache_dir cache_size cache_file
    user_input_hash=$(echo -n "$user_input" | md5sum | cut -d ' ' -f 1)
    cache_dir=${ACSH_CACHE_DIR:-"$HOME/.autocomplete/cache"}
    cache_size=${ACSH_CACHE_SIZE:-100}
    cache_file="$cache_dir/acsh-$user_input_hash.txt"

    if [[ -d "$cache_dir" && "$cache_size" -gt 0 && -f "$cache_file" ]]; then
        completions=$(cat "$cache_file" || true)
        touch "$cache_file"
    else
        echo
        echo -e "\e[90mGenerating suggestions...\e[0m"
        completions=$(openai_completion "$user_input" || true)

        if [[ -z "$completions" ]]; then
            echo
            echo_error "Failed to generate completions"
            return
        fi

        if [[ -d "$cache_dir" && "$cache_size" -gt 0 ]]; then
            echo "$completions" > "$cache_file"
            while [[ $(list_cache | wc -l) -gt "$cache_size" ]]; do
                oldest=$(list_cache | head -n 1 | cut -d ' ' -f 2-)
                rm "$oldest" || true
            done
        fi
    fi

    # Show interactive menu and execute selected command
    if [[ -n "$completions" ]]; then
        _interactive_completion_menu "$completions" "$show_explanations"

        # Clear the readline buffer after execution
        READLINE_LINE=""
        READLINE_POINT=0
    fi
}

###############################################################################
#                     CLI Commands & Configuration Management                 #
###############################################################################

show_help() {
    echo_green "Autocomplete.sh - LLM Powered Bash Completion"
    echo "Usage: autocomplete [options] command"
    echo "       autocomplete [options] install|remove|config|model|enable|disable|safeguard|clear|usage|system|command|fep|--help"
    echo
    echo "Autocomplete.sh enhances bash completion with LLM capabilities."
    echo
    echo -e "\e[1;32mUsage:\e[0m"
    echo "  - Press Tab twice for suggestions (standard completion)"
    echo "  - Press Ctrl+Space for interactive menu (navigate with ↑/↓, Enter to execute)"
    echo "  - Add '--explain' to your command to show explanations in the interactive menu"
    echo "  - AI-powered safeguards detect harmful commands and require confirmation"
    echo "  - Harm assessments are cached for instant feedback on repeated commands"
    echo
    echo "Commands:"
    echo "  command             Run autocomplete (simulate double Tab)"
    echo "  command --dry-run   Show prompt without executing"
    echo "  fep [context]        Fix error please - analyze last failed command and suggest fix (uses configured API/model)"
    echo "  model               Change language model"
    echo "  usage               Display usage stats"
    echo "  system              Display system information"
    echo "  config              Show or set configuration values"
    echo "    config set <key> <value>  Set a config value"
    echo "    config reset             Reset config to defaults"
    echo "  install             Install autocomplete to .bashrc"
    echo "  remove              Remove installation from .bashrc"
    echo "  enable              Enable autocomplete"
    echo "  disable             Disable autocomplete"
    echo "  safeguard <action>  Manage harmful command detection"
    echo "    enable            Enable safeguards"
    echo "    disable           Disable safeguards"
    echo "    status            Show safeguard status"
    echo "  clear               Clear cache and log files"
    echo "  --help              Show this help message"
    echo
    echo "Submit issues at: https://github.com/closedloop-technologies/autocomplete-sh/issues"
}

is_subshell() {
    if [[ "$$" != "$BASHPID" ]]; then
        return 0
    else
        return 1
    fi
}

is_being_sourced() {
    # Check if the script is being sourced (return 0) or executed (return 1)
    # When sourced, BASH_SOURCE[0] != $0 (or $0 is the shell name like "-bash")
    [[ "${BASH_SOURCE[0]}" != "${0}" ]]
}

show_config() {
    local config_file="$HOME/.autocomplete/config" term_width small_table
    echo_green "Autocomplete.sh - Configuration and Settings - Version $ACSH_VERSION"
    if ! is_being_sourced; then
        echo "  STATUS: Unknown - completion state cannot be checked from a subprocess."
        echo "  Run 'source autocomplete config' to check status in your current shell."
        return
    elif is_subshell; then
        echo "  STATUS: Unknown. Run 'source autocomplete config' to check status."
        return
    elif check_if_enabled; then
        echo -e "  STATUS: \033[32;5mEnabled\033[0m"
    else
        echo -e "  STATUS: \033[31;5mDisabled\033[0m - Run 'source autocomplete config' to verify."
    fi
    if [ ! -f "$config_file" ]; then
        echo_error "Configuration file not found: $config_file. Run autocomplete install."
        return
    fi
    acsh_load_config
    term_width=$(tput cols)
    if [[ $term_width -gt 70 ]]; then
        term_width=70; small_table=0
    fi
    if [[ $term_width -lt 40 ]]; then
        term_width=70; small_table=1
    fi
    for config_var in $(compgen -v | grep ACSH_); do
        if [[ $config_var == "ACSH_INPUT" || $config_var == "ACSH_PROMPT" || $config_var == "ACSH_RESPONSE" ]]; then
            continue
        fi
        config_value="${!config_var}"
        if [[ ${config_var: -8} == "_API_KEY" ]]; then
            continue
        fi
        echo -en "  $config_var:\e[90m"
        if [[ $small_table -eq 1 ]]; then
            echo -e "\n  $config_value\e[0m"
        else
            printf '%s%*s' "" $((term_width - ${#config_var} - ${#config_value} - 3)) ''
            echo -e "$config_value\e[0m"
        fi
    done
    echo -e "  ===================================================================="
    for config_var in $(compgen -v | grep ACSH_); do
        if [[ $config_var == "ACSH_INPUT" || $config_var == "ACSH_PROMPT" || $config_var == "ACSH_RESPONSE" ]]; then
            continue
        fi
        if [[ ${config_var: -8} != "_API_KEY" ]]; then
            continue
        fi
        echo -en "  $config_var:\e[90m"
        if [[ -z ${!config_var} ]]; then
            config_value="UNSET"
            echo -en "\e[31m"
        else
            rest=${!config_var:4}
            config_value="${!config_var:0:4}...${rest: -4}"
            echo -en "\e[32m"
        fi
        if [[ $small_table -eq 1 ]]; then
            echo -e "\n  $config_value\e[0m"
        else
            printf '%s%*s' "" $((term_width - ${#config_var} - ${#config_value} - 3)) ''
            echo -e "$config_value\e[0m"
        fi
    done
}

set_config() {
    local key="$1" value="$2" config_file="$HOME/.autocomplete/config"
    key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    key=$(echo "$key" | tr '[:lower:]' '[:upper:]' | sed 's/[^A-Z0-9]/_/g')
    if [ -z "$key" ]; then
        echo_error "SyntaxError: expected 'autocomplete config set <key> <value>'"
        return
    fi
    if [ ! -f "$config_file" ]; then
        echo_error "Configuration file not found: $config_file. Run autocomplete install."
        return
    fi
    sed -i "s|^\($key:\).*|\1 $value|" "$config_file"
    acsh_load_config
}

config_command() {
    local command config_file="$HOME/.autocomplete/config"
    command="${*:2}"
    if [ -z "$command" ]; then
        show_config
        return
    fi
    if [ "$2" == "set" ]; then
        local key="$3" value="$4"
        echo "Setting configuration key '$key' to '$value'"
        set_config "$key" "$value"
        echo_green "Configuration updated. Run 'autocomplete config' to view changes."
        return
    fi
    if [[ "$command" == "reset" ]]; then
        echo "Resetting configuration to default values."
        rm "$config_file" || true
        build_config
        return
    fi
    echo_error "SyntaxError: expected 'autocomplete config set <key> <value>' or 'autocomplete config reset'"
}

build_config() {
    local config_file="$HOME/.autocomplete/config" default_config
    if [ ! -f "$config_file" ]; then
        echo "Creating default configuration file at ~/.autocomplete/config"
        default_config="# ~/.autocomplete/config

# OpenAI API Key
openai_api_key: $OPENAI_API_KEY

# Anthropic API Key
anthropic_api_key: $ANTHROPIC_API_KEY

# Groq API Key
groq_api_key: $GROQ_API_KEY

# Custom API Key for Ollama
custom_api_key: $LLM_API_KEY

# Model configuration
provider: openai
model: gpt-4o
temperature: 0.0
endpoint: https://api.openai.com/v1/chat/completions
api_prompt_cost: 0.000005
api_completion_cost: 0.000015

# Max history and recent files
max_history_commands: 20
max_recent_files: 20

# Cache settings
cache_dir: $HOME/.autocomplete/cache
cache_size: 10

# Logging settings
log_file: $HOME/.autocomplete/autocomplete.log

# Harm detection settings
harm_detection_enabled: true
harm_cache_dir: $HOME/.autocomplete/harm_cache
harm_cache_size: 100
harm_timeout: 3"
        echo "$default_config" > "$config_file"
    fi
}

acsh_load_config() {
    local config_file="$HOME/.autocomplete/config" key value
    if [ -f "$config_file" ]; then
        while IFS=':' read -r key value; do
            if [[ $key =~ ^# ]] || [[ -z $key ]]; then
                continue
            fi
            key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            key=$(echo "$key" | tr '[:lower:]' '[:upper:]' | sed 's/[^A-Z0-9]/_/g')
            if [[ -n $value ]]; then
                export "ACSH_$key"="$value"
            fi
        done < "$config_file"
        if [[ -z "$ACSH_OPENAI_API_KEY" && -n "$OPENAI_API_KEY" ]]; then
            export ACSH_OPENAI_API_KEY="$OPENAI_API_KEY"
        fi
        if [[ -z "$ACSH_ANTHROPIC_API_KEY" && -n "$ANTHROPIC_API_KEY" ]]; then
            export ACSH_ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
        fi
        if [[ -z "$ACSH_GROQ_API_KEY" && -n "$GROQ_API_KEY" ]]; then
            export ACSH_GROQ_API_KEY="$GROQ_API_KEY"
        fi
        if [[ -z "$ACSH_OLLAMA_API_KEY" && -n "$LLM_API_KEY" ]]; then
            export ACSH_OLLAMA_API_KEY="$LLM_API_KEY"
        fi
        # If the custom API key was set, map it to OLLAMA if needed.
        if [[ -z "$ACSH_OLLAMA_API_KEY" && -n "$ACSH_CUSTOM_API_KEY" ]]; then
            export ACSH_OLLAMA_API_KEY="$ACSH_CUSTOM_API_KEY"
        fi
        case "${ACSH_PROVIDER:-openai}" in
            "openai") export ACSH_ACTIVE_API_KEY="$ACSH_OPENAI_API_KEY" ;;
            "anthropic") export ACSH_ACTIVE_API_KEY="$ACSH_ANTHROPIC_API_KEY" ;;
            "groq") export ACSH_ACTIVE_API_KEY="$ACSH_GROQ_API_KEY" ;;
            "ollama") export ACSH_ACTIVE_API_KEY="$ACSH_OLLAMA_API_KEY" ;;
            *) echo_error "Unknown provider: $ACSH_PROVIDER" ;;
        esac
    else
        echo "Configuration file not found: $config_file"
    fi
}

install_command() {
    local bashrc_file="$HOME/.bashrc" autocomplete_setup="source autocomplete enable" autocomplete_cli_setup="complete -F _autocompletesh_cli autocomplete"
    if ! command -v autocomplete &>/dev/null; then
        echo_error "autocomplete.sh not in PATH. Follow install instructions at https://github.com/closedloop-technologies/autocomplete-sh"
        return
    fi
    if [[ ! -d "$HOME/.autocomplete" ]]; then
        echo "Creating ~/.autocomplete directory"
        mkdir -p "$HOME/.autocomplete"
    fi
    local cache_dir=${ACSH_CACHE_DIR:-"$HOME/.autocomplete/cache"}
    if [[ ! -d "$cache_dir" ]]; then
        mkdir -p "$cache_dir"
    fi
    build_config
    acsh_load_config
    if ! grep -qF "$autocomplete_setup" "$bashrc_file"; then
        echo -e "# Autocomplete.sh" >> "$bashrc_file"
        echo -e "$autocomplete_setup\n" >> "$bashrc_file"
        echo "Added autocomplete.sh setup to $bashrc_file"
    else
        echo "Autocomplete.sh setup already exists in $bashrc_file"
    fi
    if ! grep -qF "$autocomplete_cli_setup" "$bashrc_file"; then
        echo -e "# Autocomplete.sh CLI" >> "$bashrc_file"
        echo -e "$autocomplete_cli_setup\n" >> "$bashrc_file"
        echo "Added autocomplete CLI completion to $bashrc_file"
    fi
    echo
    echo_green "Autocomplete.sh - Version $ACSH_VERSION installation complete."
    echo -e "Run: source $bashrc_file to enable autocomplete."
    echo -e "Then run: autocomplete model to select a language model."
}

remove_command() {
    local config_file="$HOME/.autocomplete/config" cache_dir=${ACSH_CACHE_DIR:-"$HOME/.autocomplete/cache"} log_file=${ACSH_LOG_FILE:-"$HOME/.autocomplete/autocomplete.log"} bashrc_file="$HOME/.bashrc"
    echo_green "Removing Autocomplete.sh installation..."
    [ -f "$config_file" ] && { rm "$config_file"; echo "Removed: $config_file"; }
    [ -d "$cache_dir" ] && { rm -rf "$cache_dir"; echo "Removed: $cache_dir"; }
    [ -f "$log_file" ] && { rm "$log_file"; echo "Removed: $log_file"; }
    if [ -d "$HOME/.autocomplete" ]; then
        if [ -z "$(ls -A "$HOME/.autocomplete")" ]; then
            rmdir "$HOME/.autocomplete"
            echo "Removed: $HOME/.autocomplete"
        else
            echo "Skipped removing $HOME/.autocomplete (not empty)"
        fi
    fi
    if [ -f "$bashrc_file" ]; then
        if grep -qF "source autocomplete enable" "$bashrc_file"; then
            sed -i '/# Autocomplete.sh/d' "$bashrc_file"
            sed -i '/autocomplete/d' "$bashrc_file"
            echo "Removed autocomplete.sh setup from $bashrc_file"
        fi
    fi
    local autocomplete_script
    autocomplete_script=$(command -v autocomplete)
    if [ -n "$autocomplete_script" ]; then
        echo "Autocomplete script is at: $autocomplete_script"
        if [ "$1" == "-y" ]; then
            rm "$autocomplete_script"
            echo "Removed: $autocomplete_script"
        else
            read -r -p "Remove the autocomplete script? (y/n): " confirm
            if [[ $confirm == "y" ]]; then
                rm "$autocomplete_script"
                echo "Removed: $autocomplete_script"
            fi
        fi
    fi
    echo "Uninstallation complete."
}

check_if_enabled() {
    local is_enabled
    is_enabled=$(complete -p | grep _autocompletesh | grep -cv _autocompletesh_cli)
    (( is_enabled > 0 )) && return 0 || return 1
}

_autocompletesh_cli() {
    if [[ -n "${COMP_WORDS[*]}" ]]; then
        command="${COMP_WORDS[0]}"
        if [[ -n "$COMP_CWORD" && "$COMP_CWORD" -lt "${#COMP_WORDS[@]}" ]]; then
            current="${COMP_WORDS[COMP_CWORD]}"
        fi
    fi
    if [[ $current == "config" ]]; then
        readarray -t COMPREPLY <<< "set
reset"
        return
    elif [[ $current == "command" ]]; then
        readarray -t COMPREPLY <<< "command --dry-run"
        return
    elif [[ $current == "safeguard" ]]; then
        readarray -t COMPREPLY <<< "enable
disable
status"
        return
    fi
    if [[ -z "$current" ]]; then
        readarray -t COMPREPLY <<< "install
remove
config
enable
disable
safeguard
clear
usage
system
command
fep
model
--help"
    fi
}

_check_command_with_safeguard() {
    local cmd_name="$1"
    shift
    local full_cmd="$cmd_name $*"

    # Check if safeguards are enabled - read directly from config file
    local config_file="$HOME/.autocomplete/config"
    local safeguards_enabled="true"  # default
    if [ -f "$config_file" ]; then
        safeguards_enabled=$(grep "^harm_detection_enabled:" "$config_file" | awk '{print $2}' | tr -d ' ')
        [[ -z "$safeguards_enabled" ]] && safeguards_enabled="true"
    fi
    if [[ "$safeguards_enabled" != "true" ]]; then
        return 0
    fi

    # Prevent infinite recursion - skip check if already inside safeguard
    if [[ -n "${_ACSH_IN_SAFEGUARD:-}" ]]; then
        return 0
    fi

    # Set flag to prevent re-entry
    export _ACSH_IN_SAFEGUARD=1

    # Check for harm using LLM
    local harm_data is_harmful explanation
    harm_data=$(detect_command_harm "$full_cmd")
    is_harmful=$(echo "$harm_data" | jq -r '.is_harmful')
    explanation=$(echo "$harm_data" | jq -r '.explanation')

    # Clear flag before prompting user (so user commands work normally)
    unset _ACSH_IN_SAFEGUARD

    if [[ "$is_harmful" == "true" ]]; then
        echo -e "\e[1;33m⚠ WARNING: Potentially harmful command detected!\e[0m"
        echo -e "\e[1;32m▶ Command:\e[0m $full_cmd"
        echo -e "\e[1;90m▶ Reason:\e[0m $explanation"
        echo
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "\e[90mCommand cancelled.\e[0m"
            return 1
        fi
    fi
    return 0
}

_enable_safeguards() {
    # Save original commands if not already saved
    local risky_commands=("rm" "dd" "mkfs" "shutdown" "reboot" "chmod" "chown" "curl" "wget")

    for cmd in "${risky_commands[@]}"; do
        local cmd_path
        cmd_path=$(type -p "$cmd" 2>/dev/null)

        # Only wrap if command exists and isn't already wrapped
        if [[ -n "$cmd_path" ]] && ! type -t "_original_$cmd" &>/dev/null; then
            eval "_original_$cmd() { $cmd_path \"\$@\"; }"

            # Create wrapper function
            eval "$cmd() {
                if _check_command_with_safeguard \"$cmd\" \"\$@\"; then
                    _original_$cmd \"\$@\"
                else
                    return 1
                fi
            }"
        fi
    done

    # Export the check function and wrappers
    export -f _check_command_with_safeguard
    for cmd in "${risky_commands[@]}"; do
        [[ $(type -t "$cmd") == "function" ]] && export -f "$cmd"
    done
}

_disable_safeguards() {
    # Restore original commands
    local risky_commands=("rm" "dd" "mkfs" "shutdown" "reboot" "chmod" "chown" "curl" "wget")

    for cmd in "${risky_commands[@]}"; do
        if type -t "_original_$cmd" &>/dev/null; then
            unset -f "$cmd"
            unset -f "_original_$cmd"
        fi
    done

    # Unset the check function
    [[ $(type -t _check_command_with_safeguard) == "function" ]] && unset -f _check_command_with_safeguard
}

enable_command() {
    if check_if_enabled; then
        echo_green "Reloading Autocomplete.sh..."
        disable_command
    fi
    acsh_load_config
    complete -D -E -F _autocompletesh -o nospace

    # Bind Ctrl+Space to interactive autocomplete widget
    bind -x '"\C-@": _interactive_autocomplete_widget'

    # FEP: capture last command and exit code after each command via PROMPT_COMMAND
    if [[ "$PROMPT_COMMAND" != *"_acsh_capture_command_result"* ]]; then
        if [[ -n "$PROMPT_COMMAND" ]]; then
            PROMPT_COMMAND="_acsh_capture_command_result; $PROMPT_COMMAND"
        else
            PROMPT_COMMAND="_acsh_capture_command_result"
        fi
        export PROMPT_COMMAND
    fi

    # FEP shortcut: allow user to just type "fep" instead of "autocomplete fep"
    fep() {
        autocomplete fep "$@"
    }
    export -f fep

    # Enable safeguard for risky commands
    _enable_safeguards

    echo_green "Interactive autocomplete enabled!"
    echo -e "\e[90mPress Ctrl+Space for interactive suggestions (add '--explain' for explanations)\e[0m"
    echo -e "\e[90mAI-powered safeguards enabled: harmful commands will require confirmation\e[0m"
}

disable_command() {
    if check_if_enabled; then
        complete -F _completion_loader -D
    fi
    # Remove FEP capture from PROMPT_COMMAND
    if [[ -n "$PROMPT_COMMAND" ]]; then
        PROMPT_COMMAND="${PROMPT_COMMAND//_acsh_capture_command_result/}"
        PROMPT_COMMAND="${PROMPT_COMMAND//;;/;}"
        PROMPT_COMMAND="${PROMPT_COMMAND#;}"
        PROMPT_COMMAND="${PROMPT_COMMAND%;}"
        export PROMPT_COMMAND
    fi
    # Remove fep shortcut
    unset -f fep 2>/dev/null
    _disable_safeguards
}

command_command() {
    local args=("$@")
    for ((i = 0; i < ${#args[@]}; i++)); do
        if [ "${args[i]}" == "--dry-run" ]; then
            args[i]=""
            _build_prompt "${args[@]}"
            return
        fi
    done
    openai_completion "$@" || true
    echo
}

clear_command() {
    local cache_dir=${ACSH_CACHE_DIR:-"$HOME/.autocomplete/cache"}
    local harm_cache_dir=${ACSH_HARM_CACHE_DIR:-"$HOME/.autocomplete/harm_cache"}
    local log_file=${ACSH_LOG_FILE:-"$HOME/.autocomplete/autocomplete.log"}

    echo "This will clear the cache, harm detection cache, and log file."
    echo -e "Completion cache: \e[31m$cache_dir\e[0m"
    echo -e "Harm cache: \e[31m$harm_cache_dir\e[0m"
    echo -e "Log file: \e[31m$log_file\e[0m"
    read -r -p "Are you sure? (y/n): " confirm
    if [[ $confirm != "y" ]]; then
        echo "Aborted."
        return
    fi

    # Clear completion cache
    if [ -d "$cache_dir" ]; then
        local cache_files
        cache_files=$(list_cache)
        if [ -n "$cache_files" ]; then
            while read -r line; do
                file=$(echo "$line" | cut -d ' ' -f 2-)
                rm "$file"
                echo "Removed: $file"
            done <<< "$cache_files"
            echo "Cleared cache in: $cache_dir"
        else
            echo "Cache is empty."
        fi
    fi

    # Clear harm detection cache
    if [ -d "$harm_cache_dir" ]; then
        local harm_cache_count
        harm_cache_count=$(find "$harm_cache_dir" -name "harm-*.json" 2>/dev/null | wc -l)
        if [ "$harm_cache_count" -gt 0 ]; then
            rm "$harm_cache_dir"/harm-*.json 2>/dev/null
            echo "Cleared $harm_cache_count harm detection cache entries from: $harm_cache_dir"
        else
            echo "Harm detection cache is empty."
        fi
    fi

    # Clear log file
    [ -f "$log_file" ] && { rm "$log_file"; echo "Removed: $log_file"; }
}

safeguard_command() {
    local action="$1"
    local config_file="$HOME/.autocomplete/config"

    case "$action" in
        enable)
            if [ -f "$config_file" ]; then
                # Check if line exists, if not add it
                if ! grep -q "^harm_detection_enabled:" "$config_file"; then
                    echo "" >> "$config_file"
                    echo "# Harm detection settings" >> "$config_file"
                    echo "harm_detection_enabled: true" >> "$config_file"
                else
                    # Update existing line
                    sed -i 's/^harm_detection_enabled:.*/harm_detection_enabled: true/' "$config_file"
                fi
                echo_green "Safeguards enabled!"
                echo -e "\e[90mHarmful commands will now require confirmation before execution.\e[0m"
                echo -e "\e[90mChanges take effect immediately.\e[0m"
            else
                echo_error "Configuration file not found: $config_file"
            fi
            ;;
        disable)
            if [ -f "$config_file" ]; then
                # Check if line exists, if not add it
                if ! grep -q "^harm_detection_enabled:" "$config_file"; then
                    echo "" >> "$config_file"
                    echo "# Harm detection settings" >> "$config_file"
                    echo "harm_detection_enabled: false" >> "$config_file"
                else
                    # Update existing line
                    sed -i 's/^harm_detection_enabled:.*/harm_detection_enabled: false/' "$config_file"
                fi
                echo_green "Safeguards disabled!"
                echo -e "\e[90mCommands will execute without harm detection checks.\e[0m"
                echo -e "\e[90mChanges take effect immediately.\e[0m"
            else
                echo_error "Configuration file not found: $config_file"
            fi
            ;;
        status)
            local status="true"  # default
            if [ -f "$config_file" ]; then
                # Read directly from config file
                status=$(grep "^harm_detection_enabled:" "$config_file" | awk '{print $2}' | tr -d ' ')
                # If not found in config, use default
                [[ -z "$status" ]] && status="true"
            fi
            if [ "$status" = "true" ]; then
                echo -e "Safeguards: \e[1;32menabled\e[0m"
            else
                echo -e "Safeguards: \e[1;31mdisabled\e[0m"
            fi
            ;;
        *)
            echo "Usage: autocomplete safeguard <enable|disable|status>"
            echo "  enable  - Enable harmful command detection"
            echo "  disable - Disable harmful command detection"
            echo "  status  - Show current safeguard status"
            ;;
    esac
}

usage_command() {
    local log_file=${ACSH_LOG_FILE:-"$HOME/.autocomplete/autocomplete.log"} cache_dir=${ACSH_CACHE_DIR:-"$HOME/.autocomplete/cache"}
    local cache_size number_of_lines api_cost avg_api_cost
    cache_size=$(list_cache | wc -l)
    echo_green "Autocomplete.sh - Usage Information"
    echo
    echo -n "Log file: "; echo -e "\e[90m$log_file\e[0m"
    if [ ! -f "$log_file" ]; then
        number_of_lines=0
        api_cost=0
        avg_api_cost=0
    else
        number_of_lines=$(wc -l < "$log_file")
        api_cost=$(awk -F, '{sum += $5} END {print sum}' "$log_file")
        avg_api_cost=$(echo "$api_cost / $number_of_lines" | bc -l)
    fi
    echo
    echo -e "\tUsage count:\t\e[32m$number_of_lines\e[0m"
    echo -e "\tAvg Cost:\t\$$(printf "%.4f" "$avg_api_cost")"
    echo -e "\tTotal Cost:\t\e[31m\$$(printf "%.4f" "$api_cost")\e[0m"
    echo
    echo -n "Cache Size: $cache_size of ${ACSH_CACHE_SIZE:-10} in "; echo -e "\e[90m$cache_dir\e[0m"
    echo "To clear log and cache, run: autocomplete clear"
}

###############################################################################
#                      Enhanced Interactive Menu UX                           #
###############################################################################

get_key() {
    IFS= read -rsn1 key 2>/dev/null >&2
    if [[ $key == $'\x1b' ]]; then
        read -rsn2 key
        if [[ $key == [A ]]; then echo up; fi
        if [[ $key == [B ]]; then echo down; fi
        if [[ $key == [C ]]; then echo right; fi
        if [[ $key == [D ]]; then echo left; fi
        if [[ $key == q ]]; then echo q; fi
    elif [[ $key == "q" ]]; then
        echo q
    elif [[ $key == $'\x7f' || $key == $'\x08' ]]; then
        echo backspace
    else
        echo "$key"
    fi
}

_interactive_completion_menu() {
    local completions_str="$1"
    local show_explanations="${2:-false}"
    local options=()
    local explanations=()

    # Parse completions into arrays (format: "command|||explanation")
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            # Check if separator exists
            if [[ "$line" == *"|||"* ]]; then
                local cmd="${line%%|||*}"
                local exp="${line#*|||}"
                options+=("$cmd")
                explanations+=("$exp")
            else
                # Old format without explanation
                options+=("$line")
                explanations+=("")
            fi
        fi
    done <<< "$completions_str"

    # If no options, return
    if [[ ${#options[@]} -eq 0 ]]; then
        return 1
    fi

    local selected=0
    local key

    # Display the interactive menu
    echo
    echo -e "\e[1;36m╔════════════════════════════════════════════════════════════════════╗\e[0m"
    echo -e "\e[1;36m║\e[0m  \e[1;32mAutocomplete Suggestions\e[0m                                        \e[1;36m║\e[0m"
    echo -e "\e[1;36m╠════════════════════════════════════════════════════════════════════╣\e[0m"
    echo -e "\e[1;36m║\e[0m  \e[90mUse ↑/↓ to navigate, Enter to execute, Esc to cancel\e[0m          \e[1;36m║\e[0m"
    echo -e "\e[1;36m╚════════════════════════════════════════════════════════════════════╝\e[0m"
    echo

    show_menu() {
        for i in "${!options[@]}"; do
            if [[ $i -eq $selected ]]; then
                # Selected: bold green command
                echo -e "  \e[1;32m▶ ${options[i]}\e[0m"
                if [[ "$show_explanations" == "true" && -n "${explanations[i]}" ]]; then
                    # Explanation: light grey (same as deselected)
                    echo -e "    \e[37m${explanations[i]}\e[0m"
                fi
            else
                # Deselected: green command
                echo -e "    \e[32m${options[i]}\e[0m"
                if [[ "$show_explanations" == "true" && -n "${explanations[i]}" ]]; then
                    # Explanation: light grey
                    echo -e "    \e[37m${explanations[i]}\e[0m"
                fi
            fi
            # Add blank line between options (except after the last one, and only if showing explanations)
            if [[ "$show_explanations" == "true" && $i -lt $((${#options[@]} - 1)) ]]; then
                echo
            fi
        done
    }

    clear_menu() {
        # Calculate total number of menu lines
        local num_lines=0
        for i in "${!options[@]}"; do
            ((num_lines++))  # Command line
            if [[ "$show_explanations" == "true" && -n "${explanations[i]}" ]]; then
                ((num_lines++))  # Explanation line
            fi
            # Blank line between options (except after the last one, and only if showing explanations)
            if [[ "$show_explanations" == "true" && $i -lt $((${#options[@]} - 1)) ]]; then
                ((num_lines++))
            fi
        done

        # Move cursor up all at once, then clear from cursor down
        tput cuu $num_lines  # Move cursor up N lines at once
        tput ed              # Clear from cursor to end of screen
    }

    # Initial menu display
    show_menu

    while true; do
        # Read key without echoing
        key=$(get_key)

        case $key in
            up)
                ((selected--))
                if ((selected < 0)); then
                    selected=$((${#options[@]} - 1))
                fi
                # Clear and redraw menu
                clear_menu
                show_menu
                ;;
            down)
                ((selected++))
                if ((selected >= ${#options[@]})); then
                    selected=0
                fi
                # Clear and redraw menu
                clear_menu
                show_menu
                ;;
            q|$'\x1b')
                # Clear the menu
                clear_menu
                echo -e "\e[90mCanceled.\e[0m"
                return 1
                ;;
            "")
                # Enter key pressed - execute the command
                clear_menu
                local selected_cmd="${options[selected]}"

                # Detect harm using LLM (if safeguards are enabled)
                # Read directly from config file for immediate effect
                local config_file="$HOME/.autocomplete/config"
                local safeguards_enabled="true"  # default
                if [ -f "$config_file" ]; then
                    safeguards_enabled=$(grep "^harm_detection_enabled:" "$config_file" | awk '{print $2}' | tr -d ' ')
                    [[ -z "$safeguards_enabled" ]] && safeguards_enabled="true"
                fi
                if [[ "$safeguards_enabled" == "true" ]]; then
                    local harm_data is_harmful explanation
                    harm_data=$(detect_command_harm "$selected_cmd")
                    is_harmful=$(echo "$harm_data" | jq -r '.is_harmful')
                    explanation=$(echo "$harm_data" | jq -r '.explanation')

                    if [[ "$is_harmful" == "true" ]]; then
                        echo -e "\e[1;33m⚠ WARNING: Potentially harmful command detected!\e[0m"
                        echo -e "\e[1;32m▶ Command:\e[0m $selected_cmd"
                        echo -e "\e[1;90m▶ Reason:\e[0m $explanation"
                        echo
                        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
                        echo
                        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                            echo -e "\e[90mCommand cancelled.\e[0m"
                            return 1
                        fi
                    fi
                fi

                echo -e "\e[1;32m▶ Executing:\e[0m $selected_cmd"
                echo

                # Add to history and execute
                history -s "$selected_cmd"
                eval "$selected_cmd"

                return 0
                ;;
        esac
    done
}

menu_selector() {
    options=("$@")
    selected=0
    show_menu() {
        echo
        echo "Select a Language Model (Up/Down arrows, Enter to select, 'q' to quit):"
        for i in "${!options[@]}"; do
            if [[ $i -eq $selected ]]; then
                echo -e "\e[1;32m> ${options[i]}\e[0m"
            else
                echo "  ${options[i]}"
            fi
        done
    }
    tput sc
    while true; do
        tput rc; tput ed
        show_menu
        key=$(get_key)
        case $key in
            up)
                ((selected--))
                if ((selected < 0)); then
                    selected=$((${#options[@]} - 1))
                fi
                ;;
            down)
                ((selected++))
                if ((selected >= ${#options[@]})); then
                    selected=0
                fi
                ;;
            q)
                echo "Selection canceled."
                return 1
                ;;
            "")
                break
                ;;
        esac
    done
    clear
    return $selected
}

model_command() {
    clear
    local selected_model options=()
    if [[ $# -ne 3 ]]; then
        mapfile -t sorted_keys < <(for key in "${!_autocomplete_modellist[@]}"; do echo "$key"; done | sort)
        for key in "${sorted_keys[@]}"; do
            options+=("$key")
        done
        echo -e "\e[1;32mAutocomplete.sh - Model Configuration\e[0m"
        menu_selector "${options[@]}"
        selected_option=$?
        if [[ $selected_option -eq 1 ]]; then
            return
        fi
        selected_model="${options[selected_option]}"
        selected_value="${_autocomplete_modellist[$selected_model]}"
    else
        provider="$2"
        model_name="$3"
        selected_value="${_autocomplete_modellist["$provider:	$model_name"]}"
        if [[ -z "$selected_value" ]]; then
            echo "ERROR: Invalid provider or model name."
            return 1
        fi
    fi
    set_config "model" "$(echo "$selected_value" | jq -r '.model')"
    set_config "endpoint" "$(echo "$selected_value" | jq -r '.endpoint')"
    set_config "provider" "$(echo "$selected_value" | jq -r '.provider')"
    prompt_cost=$(echo "$selected_value" | jq -r '.prompt_cost' | awk '{printf "%.8f", $1}')
    completion_cost=$(echo "$selected_value" | jq -r '.completion_cost' | awk '{printf "%.8f", $1}')
    set_config "api_prompt_cost" "$prompt_cost"
    set_config "api_completion_cost" "$completion_cost"
    if [[ -z "$ACSH_ACTIVE_API_KEY" && ${ACSH_PROVIDER^^} != "OLLAMA" ]]; then
        echo -e "\e[34mSet ${ACSH_PROVIDER^^}_API_KEY\e[0m"
        echo "Stored in ~/.autocomplete/config"
        if [[ ${ACSH_PROVIDER^^} == "OPENAI" ]]; then
            echo "Create a new one: https://platform.openai.com/settings/profile?tab=api-keys"
        elif [[ ${ACSH_PROVIDER^^} == "ANTHROPIC" ]]; then
            echo "Create a new one: https://console.anthropic.com/settings/keys"
        elif [[ ${ACSH_PROVIDER^^} == "GROQ" ]]; then
            echo "Create a new one: https://console.groq.com/keys"
        fi
        echo -n "Enter your ${ACSH_PROVIDER^^} API Key: "
        read -sr user_api_key_input < /dev/tty
        clear
        echo -e "\e[1;32mAutocomplete.sh - Model Configuration\e[0m"
        if [[ -n "$user_api_key_input" ]]; then
            export ACSH_ACTIVE_API_KEY="$user_api_key_input"
            set_config "${ACSH_PROVIDER,,}_api_key" "$user_api_key_input"
        fi
    fi
    model="${ACSH_MODEL:-ERROR}"
    temperature=$(echo "${ACSH_TEMPERATURE:-0.0}" | awk '{printf "%.3f", $1}')
    echo -e "Provider:\t\e[90m$ACSH_PROVIDER\e[0m"
    echo -e "Model:\t\t\e[90m$model\e[0m"
    echo -e "Temperature:\t\e[90m$temperature\e[0m"
    echo
    echo -e "Cost/token:\t\e[90mprompt: \$$ACSH_API_PROMPT_COST, completion: \$$ACSH_API_COMPLETION_COST\e[0m"
    echo -e "Endpoint:\t\e[90m$ACSH_ENDPOINT\e[0m"
    echo -n "API Key:"
    if [[ -z $ACSH_ACTIVE_API_KEY ]]; then
        if [[ ${ACSH_PROVIDER^^} == "OLLAMA" ]]; then
            echo -e "\t\e[90mNot Used\e[0m"
        else
            echo -e "\t\e[31mUNSET\e[0m"
        fi
    else
        rest=${ACSH_ACTIVE_API_KEY:4}
        config_value="${ACSH_ACTIVE_API_KEY:0:4}...${rest: -4}"
        echo -e "\t\e[32m$config_value\e[0m"
    fi
    if [[ -z $ACSH_ACTIVE_API_KEY && ${ACSH_PROVIDER^^} != "OLLAMA" ]]; then
        echo "To set the API Key, run:"
        echo -e "\t\e[31mautocomplete config set api_key <your-api-key>\e[0m"
        echo -e "\t\e[31mexport ${ACSH_PROVIDER^^}_API_KEY=<your-api-key>\e[0m"
    fi
    if [[ ${ACSH_PROVIDER^^} == "OLLAMA" ]]; then
        echo "To set a custom endpoint:"
        echo -e "\t\e[34mautocomplete config set endpoint <your-url>\e[0m"
        echo "Other models can be set with:"
        echo -e "\t\e[34mautocomplete config set model <model-name>\e[0m"
    fi
    echo "To change temperature:"
    echo -e "\t\e[90mautocomplete config set temperature <temperature>\e[0m"
    echo
}

###############################################################################
#                    FEP (Fix Error Please) Command                           #
###############################################################################

fep_command() {
    acsh_load_config
    local user_context="${*:2}"
    local response recommended_cmd explanation content

    echo -e "\e[33mAnalyzing error and generating fix...\e[0m"
    echo

    response=$(fep_completion "$user_context")

    if [[ -z "$response" ]]; then
        echo_error "Failed to get response from API. Check config and API key (autocomplete config)."
        return 1
    fi

    # Extract message content by provider
    if [[ "${ACSH_PROVIDER^^}" == "ANTHROPIC" ]]; then
        content=$(echo "$response" | jq -r '.content[0].text // empty')
    elif [[ "${ACSH_PROVIDER^^}" == "OLLAMA" ]]; then
        content=$(echo "$response" | jq -r '.message.content // empty')
    else
        content=$(echo "$response" | jq -r '.choices[0].message.content // empty')
    fi

    if [[ -z "$content" ]]; then
        echo_error "Empty response from model"
        return 1
    fi

    recommended_cmd=$(echo "$content" | jq -r '.recommended_command // empty')
    explanation=$(echo "$content" | jq -r '.explanation // empty')

    if [[ -z "$recommended_cmd" ]]; then
        echo_error "Could not parse recommendation from response"
        echo "Raw response: $content"
        return 1
    fi

    echo -e "\e[32m━━━ Recommended Command ━━━\e[0m"
    echo -e "\e[1m$recommended_cmd\e[0m"
    echo
    echo -e "\e[32m━━━ Explanation ━━━\e[0m"
    echo "$explanation"
    echo

    echo -e "\e[33mRun this command? [Y/n]\e[0m"
    read -r -n 1 confirm
    echo

    if [[ "$confirm" =~ ^[Yy]$ ]] || [[ -z "$confirm" ]]; then
        echo -e "\e[90mExecuting: $recommended_cmd\e[0m"
        eval "$recommended_cmd"
    else
        echo "Cancelled."
    fi
}

acsh_run() {
    local cmd="$*"
    export ACSH_LAST_COMMAND="$cmd"
    eval "$cmd" 2>&1 | tee "$ACSH_LAST_OUTPUT_FILE"
    export ACSH_LAST_EXIT_CODE="${PIPESTATUS[0]}"
}

###############################################################################
#                              CLI ENTRY POINT                                #
###############################################################################

case "$1" in
    "--help")
        show_help
        ;;
    system)
        _system_info
        ;;
    install)
        install_command
        ;;
    remove)
        remove_command "$@"
        ;;
    clear)
        clear_command
        ;;
    safeguard)
        safeguard_command "$2"
        ;;
    usage)
        usage_command
        ;;
    model)
        model_command "$@"
        ;;
    config)
        config_command "$@"
        ;;
    enable)
        enable_command
        ;;
    disable)
        disable_command
        ;;
    command)
        command_command "$@"
        ;;
    fep)
        fep_command "$@"
        ;;
    *)
        if [[ -n "$1" ]]; then
            echo_error "Unknown command $1 - run 'autocomplete --help' for usage or visit https://autocomplete.sh"
        else
            echo_green "Autocomplete.sh - LLM Powered Bash Completion - Version $ACSH_VERSION - https://autocomplete.sh"
        fi
        ;;
esac