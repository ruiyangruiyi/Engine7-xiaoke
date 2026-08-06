import Vision
import AppKit
import Foundation

// vision_ocr.swift — macOS Vision OCR
// 用法: swift vision_ocr.swift <image_path>
// 输出: y坐标|识别文字（y从下到上0~1，越接近1越靠顶部）

let args = CommandLine.arguments
let imagePath = args.count > 1 ? args[1] : "/tmp/screenshot.png"

guard let img = NSImage(contentsOfFile: imagePath) else {
    fputs("Error: cannot load image: \(imagePath)\n", stderr)
    exit(1)
}
var rect = CGRect.zero
guard let cgImg = img.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
    fputs("Error: cannot get CGImage\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en"]

let handler = VNImageRequestHandler(cgImage: cgImg)
try? handler.perform([request])

for obs in request.results ?? [] {
    if let candidate = obs.topCandidates(1).first {
        let bbox = obs.boundingBox
        print(String(format: "%.2f|%@", bbox.origin.y, candidate.string))
    }
}
