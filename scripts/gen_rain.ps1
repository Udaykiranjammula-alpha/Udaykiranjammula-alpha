# Matrix Rain SVG Generator — SMIL Animations (GitHub-compatible)
# GitHub strips CSS @keyframes from <img src=".svg"> — SMIL works natively

$chars     = @('0','1','&lt;','&gt;','&amp;','{','}','(',')',';',':','/','|','#','@','$','%','*','~','=','+','_','.','A','B','C','D','E','F')
$colors    = @('#7aa2f7','#bb9af7','#7dcfff','#9ece6a','#b4f9f8','#bb9af7','#7aa2f7')
$dimColors = @('#292e42','#3b4261','#1f2335','#414868')

$columns = 55
$width   = 1200
$height  = 180
$colW    = [math]::Round($width / $columns)

$rng = New-Object System.Random

$groups = ""
for ($i = 0; $i -lt $columns; $i++) {
    $x     = $i * $colW + [math]::Round($colW / 2)
    $color = $colors[$i % $colors.Length]
    $dim   = $dimColors[$i % $dimColors.Length]
    $n     = $rng.Next(6, 12)
    $speed = [math]::Round(1.8 + $rng.NextDouble() * 2.8, 2)
    # Negative begin = start mid-animation so columns are staggered on first load
    $delay = -[math]::Round($rng.NextDouble() * $speed, 2)

    $groups += "<g font-family='monospace' font-size='14px' text-anchor='middle'>`n"
    for ($j = 0; $j -lt $n; $j++) {
        $char = $chars[$rng.Next(0, $chars.Length)]
        $y    = $j * 16
        if ($j -eq 0) {
            # Bright white head
            $groups += "  <text x='$x' y='$y' fill='#e0f2fe' opacity='1'>$char</text>`n"
        } elseif ($j -eq 1) {
            $groups += "  <text x='$x' y='$y' fill='$color' opacity='0.95'>$char</text>`n"
        } elseif ($j -lt 4) {
            $op = [math]::Round(0.85 - ($j - 2) * 0.18, 2)
            $groups += "  <text x='$x' y='$y' fill='$color' opacity='$op'>$char</text>`n"
        } else {
            $op = [math]::Round(0.5 - ($j - 4) * 0.08, 2)
            if ($op -lt 0.08) { $op = 0.08 }
            $groups += "  <text x='$x' y='$y' fill='$dim' opacity='$op'>$char</text>`n"
        }
    }
    # SMIL translateY animation — from above canvas to below canvas
    $groups += "  <animateTransform attributeName='transform' type='translate' from='0,-170' to='0,220' dur='${speed}s' repeatCount='indefinite' begin='${delay}s'/>`n"
    $groups += "</g>`n"
}

$svg = @"
<svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">
  <defs>
    <clipPath id="clip">
      <rect width="$width" height="$height"/>
    </clipPath>
  </defs>
  <rect width="$width" height="$height" fill="#1a1b26"/>
  <g clip-path="url(#clip)">
$groups  </g>
</svg>
"@

$outPath = "assets\matrix-rain.svg"
$svg | Out-File -FilePath $outPath -Encoding UTF8 -NoNewline
$size = (Get-Item $outPath).Length
Write-Host "Generated: $outPath  ($size bytes, $columns columns, SMIL animations)"
