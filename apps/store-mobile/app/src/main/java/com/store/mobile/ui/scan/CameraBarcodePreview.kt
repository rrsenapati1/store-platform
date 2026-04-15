package com.store.mobile.ui.scan

import android.content.Context
import android.content.ContextWrapper
import androidx.activity.ComponentActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.common.InputImage
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

@Composable
fun CameraBarcodePreview(
    modifier: Modifier = Modifier,
    onBarcodeDetected: (String) -> Unit,
    onCameraFailure: (String) -> Unit,
) {
    val context = LocalContext.current
    val activity = remember(context) { context.findComponentActivity() }
    val cameraExecutor = remember { Executors.newSingleThreadExecutor() }
    val scanner = remember { BarcodeScanning.getClient() }
    val currentOnBarcodeDetected = rememberUpdatedState(onBarcodeDetected)
    val currentOnCameraFailure = rememberUpdatedState(onCameraFailure)

    DisposableEffect(Unit) {
        onDispose {
            scanner.close()
            cameraExecutor.shutdown()
        }
    }

    AndroidView(
        modifier = modifier,
        factory = { viewContext ->
            PreviewView(viewContext).apply {
                scaleType = PreviewView.ScaleType.FILL_CENTER
                implementationMode = PreviewView.ImplementationMode.COMPATIBLE
            }.also { previewView ->
                bindPreview(
                    context = viewContext,
                    activity = activity,
                    previewView = previewView,
                    cameraExecutor = cameraExecutor,
                    scanner = scanner,
                    onBarcodeDetected = { currentOnBarcodeDetected.value(it) },
                    onCameraFailure = { currentOnCameraFailure.value(it) },
                )
            }
        },
    )
}

private fun bindPreview(
    context: Context,
    activity: ComponentActivity?,
    previewView: PreviewView,
    cameraExecutor: ExecutorService,
    scanner: com.google.mlkit.vision.barcode.BarcodeScanner,
    onBarcodeDetected: (String) -> Unit,
    onCameraFailure: (String) -> Unit,
) {
    if (activity == null) {
        onCameraFailure("Camera preview is unavailable because the activity could not be resolved.")
        return
    }

    val providerFuture = ProcessCameraProvider.getInstance(context)
    providerFuture.addListener(
        {
            try {
                val cameraProvider = providerFuture.get()
                val preview = Preview.Builder()
                    .build()
                    .also { it.setSurfaceProvider(previewView.surfaceProvider) }
                val analysis = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()
                    .also { analyzer ->
                        analyzer.setAnalyzer(cameraExecutor) { imageProxy ->
                            analyzeFrame(
                                imageProxy = imageProxy,
                                scanner = scanner,
                                onBarcodeDetected = onBarcodeDetected,
                            )
                        }
                    }

                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    activity,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    analysis,
                )
            } catch (exception: Exception) {
                onCameraFailure(
                    exception.message ?: "Camera preview failed to start.",
                )
            }
        },
        ContextCompat.getMainExecutor(context),
    )
}

@androidx.annotation.OptIn(ExperimentalGetImage::class)
private fun analyzeFrame(
    imageProxy: androidx.camera.core.ImageProxy,
    scanner: com.google.mlkit.vision.barcode.BarcodeScanner,
    onBarcodeDetected: (String) -> Unit,
) {
    val mediaImage = imageProxy.image
    if (mediaImage == null) {
        imageProxy.close()
        return
    }

    val image = InputImage.fromMediaImage(mediaImage, imageProxy.imageInfo.rotationDegrees)
    scanner.process(image)
        .addOnSuccessListener { barcodes ->
            barcodes.firstNotNullOfOrNull { it.rawValue }?.let(onBarcodeDetected)
        }
        .addOnCompleteListener {
            imageProxy.close()
        }
}

private tailrec fun Context.findComponentActivity(): ComponentActivity? {
    return when (this) {
        is ComponentActivity -> this
        is ContextWrapper -> baseContext.findComponentActivity()
        else -> null
    }
}
