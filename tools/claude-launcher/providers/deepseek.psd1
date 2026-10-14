@{
    SchemaVersion = 1
    Id = 'deepseek'
    Enabled = $true
    Backend = 'AnthropicCompatible'
    Endpoint = 'https://api.deepseek.com/anthropic'
    Auth = @{
        Kind = 'DpapiFile'
        SecretRef = 'deepseek/default'
        Variable = 'ANTHROPIC_AUTH_TOKEN'
    }
    Models = @{
        Main = 'deepseek-flash[1m]'
        Opus = 'deepseek-flash[1m]'
        Sonnet = 'deepseek-flash[1m]'
        Haiku = 'deepseek-flash'
        Subagent = 'deepseek-flash'
    }
    Runtime = @{
        Effort = 'max'
        AutoCompactWindow = 786432
    }
}
