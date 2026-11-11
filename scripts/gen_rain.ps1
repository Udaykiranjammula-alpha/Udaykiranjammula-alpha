
# Matrix Rain SVG Generator — Cyber Theme (Cyan / Violet / Magenta)
$chars = @('0','1','<','>','{','}','(',')',';',':','/','|','#','@','$','%','*','~','=','+','_','.','A','B','C','D','E','F')
$colors     = @('#06b6d4','#8b5cf6','#ec4899','#7aa2f7','#22d3ee','#a855f7','#06b6d4','#8b5cf6')
$dimColors  = @('#0e4a5a','#2d1b6e','#5e1535','#1a2f5e','#073b47','#2a0a5e','#0e4a5a','#2d1b6e')

$columns = 60
$width   = 1200
$height  = 180
$colW    = [math]::Round($width / $columns)

$rng = New-Object System.Random

$styleBlock = "<style>`n"
for ($i = 1; $i -le $columns; $i++) {
    $speed = [math]::Round(1.6 + $rng.NextDouble() * 2.4, 2)
    $delay = -[math]::Round($rng.NextDouble() * 5.0, 2)
    $styleBlock += ".c$i{animation:f$i ${speed}s linear ${delay}s infinite;}`n"
    $styleBlock += "@keyframes f$i{0%{transform:translateY(-170px);opacity:0}8%{opacity:1}88%{opacity:.8}100%{transform:translateY(230px);opacity:0}}`n"
}
$styleBlock += "</style>"

$groups = ""
for ($i = 1; $i -le $columns; $i++) {
    $x     = ($i - 1) * $colW + 4
    $color = $colors[($i - 1) % $colors.Length]
    $dim   = $dimColors[($i - 1) % $dimColors.Length]
    $n     = $rng.Next(6, 11)
    $groups += "<g class='c$i' font-family='monospace' font-size='13px' text-anchor='middle'>`n"
    for ($j = 0; $j -lt $n; $j++) {
        $char = $chars[$rng.Next(0, $chars.Length)]
        if ($j -eq 0) {
            # Bright head character
            $groups += "  <text x='$x' y='$($j * 16)' fill='#ffffff' opacity='1'>$char</text>`n"
        } elseif ($j -lt 3) {
            $op = [math]::Round(1.0 - $j * 0.15, 2)
            $groups += "  <text x='$x' y='$($j * 16)' fill='$color' opacity='$op'>$char</text>`n"
        } else {
            $op = [math]::Round(0.7 - ($j - 3) * 0.1, 2)
            if ($op -lt 0.1) { $op = 0.1 }
            $groups += "  <text x='$x' y='$($j * 16)' fill='$dim' opacity='$op'>$char</text>`n"
        }
    }
    $groups += "</g>`n"
}

$svg = @"
<svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">
  <rect width="$width" height="$height" fill="#0c0f1d"/>
  $styleBlock
  $groups
</svg>
"@

$svg | Out-File -FilePath "assets\matrix-rain.svg" -Encoding UTF8 -NoNewline
Write-Host "Done: assets\matrix-rain.svg generated ($columns columns)"
