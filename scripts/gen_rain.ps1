# Matrix Rain SVG Generator — SMIL Animations (GitHub-compatible)
# GitHub strips CSS @keyframes from <img src=".svg"> — SMIL works natively

$chars     = @('0','1','<','>','{','}','(',')',';',':','/','|','#','@','$','%','*','~','=','+','_','.','A','B','C','D','E','F')
$colors    = @('#06b6d4','#8b5cf6','#ec4899','#7aa2f7','#22d3ee','#a855f7','#06b6d4','#8b5cf6')
$dimColors = @('#0e4a5a','#2d1b6e','#5e1535','#1a2f5e','#073b47','#2a0a5e','#0e4a5a','#2d1b6e')

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
  <rect width="$width" height="$height" fill="#0c0f1d"/>
  <g clip-path="url(#clip)">
$groups  </g>
</svg>
"@

$outPath = "assets\matrix-rain.svg"
$svg | Out-File -FilePath $outPath -Encoding UTF8 -NoNewline
$size = (Get-Item $outPath).Length
Write-Host "Generated: $outPath  ($size bytes, $columns columns, SMIL animations)"
