# ArcFace Browser Implementation Guide

Detailed explanation of the face recognition pipeline running in the browser.

## Overview

This system implements **ArcFace-style face recognition** entirely in the browser using TensorFlow.js. The approach prioritizes privacy by ensuring facial images never leave the user's device - only mathematical embeddings are transmitted to the backend.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (Client-Side)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Webcam Capture                                          │
│     ↓                                                        │
│  2. Face Detection (BlazeFace)                              │
│     ↓                                                        │
│  3. Face Alignment & Preprocessing                          │
│     ↓                                                        │
│  4. Embedding Generation (FaceNet/MobileFaceNet)            │
│     ↓                                                        │
│  5. L2 Normalization                                         │
│     ↓                                                        │
│  6. Serialize to JSON                                        │
│     ↓                                                        │
│  7. Send via HTTPS → Backend                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Server-Side)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  8. Receive Embeddings (512-dim vectors)                    │
│     ↓                                                        │
│  9. Cosine Similarity Calculation                           │
│     ↓                                                        │
│  10. Threshold Matching (≥ 0.8)                             │
│     ↓                                                        │
│  11. Mark Attendance or Reject                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Pipeline Components

### 1. Webcam Capture

**Technology:** `navigator.mediaDevices.getUserMedia`

**Implementation:**
```javascript
const stream = await navigator.mediaDevices.getUserMedia({
    video: {
        width: 640,
        height: 480,
        facingMode: 'user'  // Front camera
    }
});
videoElement.srcObject = stream;
```

**Key Points:**
- Requests camera permission
- Sets resolution to 640×480 for performance
- Uses front-facing camera

### 2. Face Detection

**Model:** BlazeFace (Google)

**Why BlazeFace?**
- Lightweight (< 1MB)
- Fast (~5ms inference on CPU)
- Designed for mobile/web
- High accuracy for frontal faces

**Implementation:**
```javascript
const model = await blazeface.load();
const predictions = await model.estimateFaces(videoElement, false);

if (predictions.length > 0) {
    const face = predictions[0];
    // face.topLeft: [x, y]
    // face.bottomRight: [x, y]
    // face.landmarks: 6 key points (eyes, nose, mouth)
}
```

**Output:**
- Bounding box coordinates
- 6 facial landmarks
- Confidence score

### 3. Face Alignment & Preprocessing

**Steps:**

1. **Extract Face Region:**
```javascript
const [x, y] = face.topLeft;
const [x2, y2] = face.bottomRight;
const width = x2 - x;
const height = y2 - y;

// Add padding (30px)
const padding = 30;
const faceX = Math.max(0, x - padding);
const faceY = Math.max(0, y - padding);
const faceWidth = width + 2 * padding;
const faceHeight = height + 2 * padding;
```

2. **Resize to Model Input:**
```javascript
// FaceNet requires 160×160 input
canvas.width = 160;
canvas.height = 160;

ctx.drawImage(
    videoElement,
    faceX, faceY, faceWidth, faceHeight,  // Source
    0, 0, 160, 160                         // Destination
);
```

3. **Normalize Pixel Values:**
```javascript
const imageTensor = tf.browser.fromPixels(canvas)
    .toFloat()              // Convert to float32
    .div(255.0)             // Scale to [0, 1]
    .sub(0.5)               // Center at 0
    .mul(2.0)               // Scale to [-1, 1]
    .expandDims(0);         // Add batch dimension [1, 160, 160, 3]
```

### 4. Embedding Generation

**Model Options:**

#### Option A: FaceNet (Recommended for Production)
- **Architecture:** Inception-ResNet-v1
- **Output:** 512-dimensional embedding
- **Accuracy:** High (99.65% on LFW)
- **Model Size:** ~25MB

```javascript
// Load from TensorFlow Hub
const model = await tf.loadGraphModel(
    'https://tfhub.dev/tensorflow/tfjs-model/facenet/1/default/1',
    { fromTFHub: true }
);

const embedding = model.predict(imageTensor);
```

#### Option B: MobileFaceNet (Lightweight)
- **Architecture:** MobileNet-based
- **Output:** 128 or 512-dimensional
- **Accuracy:** Good (98.5% on LFW)
- **Model Size:** ~4MB

```javascript
const model = await tf.loadLayersModel(
    'https://path-to-mobilefacenet/model.json'
);

const embedding = model.predict(imageTensor);
```

#### Option C: Custom ArcFace Model
For maximum accuracy, convert a PyTorch/TensorFlow ArcFace model:

```python
# Python: Convert ArcFace to TensorFlow.js
import tensorflowjs as tfjs

# Load your trained ArcFace model
model = load_arcface_model('arcface_weights.h5')

# Convert to TensorFlow.js format
tfjs.converters.save_keras_model(model, 'arcface_tfjs/')
```

Then load in browser:
```javascript
const model = await tf.loadLayersModel('./arcface_tfjs/model.json');
```

### 5. L2 Normalization

**Purpose:** Normalize embeddings to unit length for cosine similarity.

**Implementation:**
```javascript
const embeddingArray = Array.from(await embeddingTensor.data());

// Calculate L2 norm
const norm = Math.sqrt(
    embeddingArray.reduce((sum, val) => sum + val * val, 0)
);

// Normalize
const normalizedEmbedding = embeddingArray.map(val => val / norm);
```

**Mathematical Formula:**

$$
\text{normalized}(x) = \frac{x}{||x||_2} = \frac{x}{\sqrt{\sum_{i=1}^{n} x_i^2}}
$$

After normalization:
- $||x||_2 = 1$ (unit length)
- Cosine similarity reduces to dot product
- Range: [-1, 1]

### 6. Serialization

**Format:** JSON array of floats

```javascript
const payload = {
    student_id: "1RV23CS288",
    live_embedding: [0.123, -0.456, 0.789, ...]  // 512 floats
};

// Send to backend
fetch('https://localhost:8000/api/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
});
```

**Data Size:**
- 512 floats × 4 bytes = 2,048 bytes ≈ 2KB
- Compared to JPEG image: ~100KB (50× smaller)

## Backend Verification

### Cosine Similarity Calculation

**Formula:**

$$
\text{similarity}(A, B) = \frac{A \cdot B}{||A||_2 \times ||B||_2}
$$

For normalized vectors (L2 norm = 1):

$$
\text{similarity}(A, B) = A \cdot B = \sum_{i=1}^{n} A_i \times B_i
$$

**Implementation (Python):**
```python
import numpy as np

def cosine_similarity(vec1, vec2):
    a = np.array(vec1)
    b = np.array(vec2)
    
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    return dot_product / (norm_a * norm_b)
```

**Range:**
- 1.0: Identical vectors
- 0.0: Orthogonal (uncorrelated)
- -1.0: Opposite vectors

**Typical Face Matching Scores:**
- Same person: 0.75 - 0.95
- Different people: 0.20 - 0.60
- Threshold: 0.80 (configurable)

### Matching Logic

**Multi-Embedding Verification:**

```python
# Student has 5 stored embeddings
stored_embeddings = [emb1, emb2, emb3, emb4, emb5]
live_embedding = received_from_frontend

# Calculate similarities
similarities = [
    cosine_similarity(live_embedding, emb)
    for emb in stored_embeddings
]
# Result: [0.85, 0.92, 0.78, 0.88, 0.81]

# Count matches above threshold (0.8)
matches = sum(1 for s in similarities if s >= 0.8)
# Result: 4 matches

# Verify if enough matches (min 2)
is_verified = matches >= 2  # True
```

**Why 5 Embeddings?**
- Captures variation in pose, lighting, expression
- Increases robustness
- Reduces false rejections

**Why 2/5 Threshold?**
- Balance between security and usability
- Allows for some variation
- Prevents single-point failure

## Performance Optimization

### Model Loading

**Strategy:** Load once, cache in memory

```javascript
let faceDetectionModel = null;
let faceRecognitionModel = null;

async function loadModels() {
    if (faceDetectionModel && faceRecognitionModel) {
        return;  // Already loaded
    }
    
    console.log('Loading models...');
    faceDetectionModel = await blazeface.load();
    faceRecognitionModel = await tf.loadGraphModel(MODEL_URL);
    console.log('Models loaded');
}

// Call once on page load
await loadModels();
```

### Inference Speed

**Benchmarks (on average laptop):**
- Face detection: ~10ms
- Embedding generation: ~50ms
- Total: ~60ms per frame

**Optimization Tips:**
1. Use WebGL backend: `tf.setBackend('webgl')`
2. Warm up models with dummy input
3. Reuse tensors where possible
4. Dispose tensors after use

```javascript
// Dispose to free GPU memory
imageTensor.dispose();
embeddingTensor.dispose();
```

### Memory Management

**Problem:** Memory leaks from tensor accumulation

**Solution:** Explicit disposal

```javascript
tf.tidy(() => {
    const imageTensor = tf.browser.fromPixels(canvas);
    const normalized = imageTensor.div(255.0).sub(0.5).mul(2.0);
    const embedding = model.predict(normalized.expandDims(0));
    
    // All intermediate tensors disposed automatically
    return embedding;
});
```

## Security Considerations

### Privacy Benefits

✅ **Raw images never transmitted**
- Only embeddings (mathematical vectors)
- Cannot reconstruct face from embedding
- GDPR-friendly

✅ **Client-side processing**
- Reduces server compute load
- Lower bandwidth usage
- Faster response time

### Security Limitations

⚠️ **Not implemented (out of scope):**
- Liveness detection (anti-spoofing)
- Presentation attack detection (PAD)
- Deep fake detection
- 3D depth verification

**Attack Vectors:**
- Photo/video replay attacks
- 3D printed masks
- Deepfake videos
- Embedding injection (mitigated by HTTPS)

**Recommendations for Production:**
- Add liveness detection (blink, head turn)
- Use depth camera (Intel RealSense, iPhone Face ID)
- Implement challenge-response (random gestures)
- Monitor for suspicious patterns

## Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome 90+ | ✅ Full | Recommended |
| Edge 90+ | ✅ Full | Chromium-based |
| Firefox 88+ | ✅ Full | Slightly slower |
| Safari 14+ | ⚠️ Partial | WebGL issues on iOS |
| Opera 76+ | ✅ Full | Chromium-based |

**Requirements:**
- WebGL 2.0 support
- WebRTC (getUserMedia)
- ES6+ JavaScript
- HTTPS (required for camera access)

## Fallback Strategies

### If Model Fails to Load

```javascript
try {
    await loadModels();
} catch (error) {
    console.error('Model loading failed:', error);
    
    // Fallback 1: Use simpler model
    faceRecognitionModel = await tf.loadLayersModel(
        'https://cdn.jsdelivr.net/npm/@tensorflow-models/mobilenet'
    );
    
    // Fallback 2: Server-side processing
    alert('Face recognition unavailable. Contact admin.');
}
```

### If Camera Access Denied

```javascript
try {
    await startWebcam();
} catch (error) {
    if (error.name === 'NotAllowedError') {
        alert('Please grant camera permission in browser settings');
    } else if (error.name === 'NotFoundError') {
        alert('No camera detected. This system requires a webcam.');
    }
}
```

## Future Improvements

### 1. True ArcFace Implementation

Current system uses FaceNet. For true ArcFace:

```python
# Train custom ArcFace model
class ArcFaceModel(nn.Module):
    def __init__(self, embedding_size=512, num_classes=420):
        super().__init__()
        self.backbone = ResNet50()
        self.arcface = ArcMarginProduct(embedding_size, num_classes)
    
    def forward(self, x, label):
        embeddings = self.backbone(x)
        output = self.arcface(embeddings, label)
        return output, embeddings
```

Convert to TensorFlow.js and deploy.

### 2. Liveness Detection

Add blink detection:
```javascript
const faceLandmarks = await facemesh.estimateFaces(video);
const leftEye = faceLandmarks.annotations.leftEyeUpper;
const rightEye = faceLandmarks.annotations.rightEyeUpper;

// Calculate eye aspect ratio (EAR)
if (EAR < threshold) {
    console.log('Blink detected - likely live person');
}
```

### 3. Progressive Web App (PWA)

Cache models offline:
```javascript
// service-worker.js
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('models-v1').then((cache) => {
            return cache.addAll([
                '/models/blazeface/model.json',
                '/models/facenet/model.json'
            ]);
        })
    );
});
```

## References

### Papers
- **ArcFace:** Deng et al. "ArcFace: Additive Angular Margin Loss for Deep Face Recognition" (CVPR 2019)
- **FaceNet:** Schroff et al. "FaceNet: A Unified Embedding for Face Recognition and Clustering" (CVPR 2015)
- **BlazeFace:** Bazarevsky et al. "BlazeFace: Sub-millisecond Neural Face Detection on Mobile GPUs" (2019)

### Libraries
- TensorFlow.js: https://www.tensorflow.org/js
- BlazeFace: https://github.com/tensorflow/tfjs-models/tree/master/blazeface
- FaceNet TFJS: https://github.com/justadudewhohacks/face-api.js

### Tools
- Model Converter: https://github.com/tensorflow/tfjs/tree/master/tfjs-converter
- TensorFlow Hub: https://tfhub.dev/
