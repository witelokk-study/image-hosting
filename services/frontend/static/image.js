const apiBase = (window.APP_CONFIG?.apiBaseUrl || "http://localhost:8080").replace(/\/$/, "");
const PREVIEW_SIZES = [256, 512, 1024];

const params = new URLSearchParams(window.location.search);
const pathId = window.location.pathname.replace(/^\/+/, "").split("/")[0];
const imageId = params.get("id") || (pathId && pathId !== "image.html" ? pathId : null);

const fileNameEl = document.getElementById("fileName");
const contentTypeEl = document.getElementById("contentType");
const fileSizeEl = document.getElementById("fileSize");
const previewImg = document.getElementById("previewImage");
const previewFallback = document.getElementById("previewFallback");
const previewLinks = document.getElementById("previewLinks");
const downloadOriginal = document.getElementById("downloadOriginal");
const imageSection = document.getElementById("imageSection");
const errorSection = document.getElementById("errorSection");
const errorText = document.getElementById("errorText");

const formatBytes = (bytes) => {
    if (!bytes && bytes !== 0) return "—";
    const units = ["B", "KB", "MB", "GB"];
    const exponent = Math.min(
        Math.floor(Math.log(bytes) / Math.log(1024)),
        units.length - 1,
    );
    const size = bytes / 1024 ** exponent;
    return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[exponent]}`;
};

const showError = (message) => {
    errorText.textContent = message;
    imageSection.classList.add("hidden");
    errorSection.classList.remove("hidden");
};

const renderPreviews = () => {
    previewLinks.innerHTML = "";
    PREVIEW_SIZES.forEach((size) => {
        const link = document.createElement("a");
        link.href = `${apiBase}/images/${encodeURIComponent(imageId)}/preview/${size}`;
        link.textContent = `${size}px`;
        link.className = "btn btn--ghost";
        link.target = "_blank";
        link.rel = "noopener";
        previewLinks.appendChild(link);
    });
};

const setPreviewImage = () => {
    previewImg.src = `${apiBase}/images/${encodeURIComponent(imageId)}/preview/512`;
    previewImg.onload = () => {
        previewImg.hidden = false;
        previewFallback.textContent = "";
    };
    previewImg.onerror = () => {
        previewImg.hidden = true;
        previewFallback.textContent = "Preview unavailable";
    };
};

const loadImage = async () => {
    if (!imageId) {
        showError("No image id provided.");
        return;
    }

    try {
        const response = await fetch(`${apiBase}/images/${encodeURIComponent(imageId)}`);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || "Image not found");
        }

        const data = await response.json();
        fileNameEl.textContent = data.original_filename || "Untitled";
        contentTypeEl.textContent = data.content_type || "Unknown";
        fileSizeEl.textContent = formatBytes(data.size_bytes);

        downloadOriginal.href = `${apiBase}/images/${encodeURIComponent(imageId)}/file`;
        renderPreviews();
        setPreviewImage();
    } catch (err) {
        console.error(err);
        showError(err.message || "Could not load image");
    }
};

loadImage();
