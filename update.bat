$headers = @{ 'User-Agent' = 'garvis-updater' }
$rel = Invoke-RestMethod `
    'https://api.github.com/repos/bous-devysek/my_dgarvis/releases/latest' `
    -Headers $headers -TimeoutSec 10
$new = $rel.tag_name.TrimStart('v')