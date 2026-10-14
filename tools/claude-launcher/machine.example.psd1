# Portable example only. Run Initialize-Machine.ps1 to create machine.local.psd1.
@{
    SchemaVersion = 1
    ClaudePath = 'C:\Tools\Claude\claude.exe'
    Secrets = @{
        'deepseek/default' = @{
            Path = 'C:\Private\OpenSci\deepseek-key.dpapi'
            AllowedEndpointHosts = @('api.deepseek.com')
        }
        'kimi/default' = @{
            Path = 'C:\Private\OpenSci\kimi-key.dpapi'
            AllowedEndpointHosts = @('api.kimi.com')
        }
    }
}
