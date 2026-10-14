@{
    SchemaVersion = 1
    Id = 'kimi'
    Enabled = $true
    Backend = 'AnthropicCompatible'
    Endpoint = 'https://api.kimi.com/coding/'
    Auth = @{ Kind = 'DpapiFile'; SecretRef = 'kimi/default'; Variable = 'ANTHROPIC_API_KEY' }
    Models = @{
        Main = 'k3-256k'
        Opus = 'k3[1m]'
        Sonnet = 'k3-256k'
        Haiku = 'k3-256k'
        Fable = 'k3-256k'
        Subagent = 'k3-256k'
        Custom = 'kimi-for-coding'
    }
    Runtime = @{ Effort = 'high'; MaxContextTokens = 262144; AutoCompactWindow = 1000000; ForceSubagent = $true }
    RestrictModels = $true
}
