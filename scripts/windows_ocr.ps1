param(
    [Parameter(Mandatory = $true)]
    [string]$ImageDirectory,
    [Parameter(Mandatory = $true)]
    [string]$OutputFile,
    [string]$Language = "zh-Hans-CN"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.FileAccessMode, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]

function Wait-WinRT {
    param(
        [Parameter(Mandatory = $true)]$Operation,
        [Parameter(Mandatory = $true)][Type]$ResultType
    )
    $method = [System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object {
            $_.Name -eq "AsTask" -and
            $_.IsGenericMethod -and
            $_.GetParameters().Count -eq 1 -and
            $_.GetParameters()[0].ParameterType.Name -eq "IAsyncOperation``1"
        } |
        Select-Object -First 1
    $task = $method.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    $task.Wait()
    return $task.Result
}

$recognizerLanguage = New-Object Windows.Globalization.Language($Language)
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($recognizerLanguage)
if ($null -eq $engine) {
    throw "Windows OCR language is not installed: $Language"
}

$imageRoot = (Resolve-Path -LiteralPath $ImageDirectory).Path
$images = Get-ChildItem -LiteralPath $imageRoot -File |
    Where-Object { $_.Extension -in ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp" } |
    Sort-Object Name

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$writer = New-Object System.IO.StreamWriter($OutputFile, $false, $utf8NoBom)

try {
    $index = 0
    foreach ($image in $images) {
        $index += 1
        $storageFile = Wait-WinRT ([Windows.Storage.StorageFile]::GetFileFromPathAsync($image.FullName)) ([Windows.Storage.StorageFile])
        $stream = Wait-WinRT ($storageFile.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        try {
            $decoder = Wait-WinRT ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
            $bitmap = Wait-WinRT ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
            try {
                if ($bitmap.PixelWidth -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension -or
                    $bitmap.PixelHeight -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension) {
                    throw "Image exceeds Windows OCR maximum dimension: $($image.Name)"
                }

                $result = Wait-WinRT ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
                $lines = @()
                foreach ($line in $result.Lines) {
                    $words = @()
                    foreach ($word in $line.Words) {
                        $rect = $word.BoundingRect
                        $words += [ordered]@{
                            text = $word.Text
                            x = [math]::Round($rect.X, 2)
                            y = [math]::Round($rect.Y, 2)
                            width = [math]::Round($rect.Width, 2)
                            height = [math]::Round($rect.Height, 2)
                        }
                    }
                    if ($words.Count -eq 0) { continue }

                    $left = ($words | ForEach-Object { $_["x"] } | Measure-Object -Minimum).Minimum
                    $top = ($words | ForEach-Object { $_["y"] } | Measure-Object -Minimum).Minimum
                    $right = ($words | ForEach-Object { $_["x"] + $_["width"] } | Measure-Object -Maximum).Maximum
                    $bottom = ($words | ForEach-Object { $_["y"] + $_["height"] } | Measure-Object -Maximum).Maximum
                    $lines += [ordered]@{
                        text = $line.Text
                        x = [math]::Round($left, 2)
                        y = [math]::Round($top, 2)
                        width = [math]::Round($right - $left, 2)
                        height = [math]::Round($bottom - $top, 2)
                        words = $words
                    }
                }

                $pageNumber = 0
                if ($image.BaseName -match "(\d+)$") {
                    $pageNumber = [int]$Matches[1]
                } else {
                    $pageNumber = $index
                }
                $page = [ordered]@{
                    page = $pageNumber
                    image = $image.Name
                    width = $bitmap.PixelWidth
                    height = $bitmap.PixelHeight
                    angle = $result.TextAngle
                    text = $result.Text
                    lines = $lines
                }
                $writer.WriteLine(($page | ConvertTo-Json -Depth 8 -Compress))
                $writer.Flush()
                Write-Progress -Activity "Windows OCR" -Status "$index / $($images.Count): $($image.Name)" -PercentComplete (($index / $images.Count) * 100)
            } finally {
                if ($null -ne $bitmap) { $bitmap.Dispose() }
            }
        } finally {
            if ($null -ne $stream) { $stream.Dispose() }
        }
    }
} finally {
    $writer.Dispose()
}
