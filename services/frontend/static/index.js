const apiBase = (window.APP_CONFIG?.apiBaseUrl || "http://localhost:8080").replace(/\/$/, "");

const fileInput = document.getElementById("fileInput");
const selectButton = document.getElementById("selectButton");
const uploadButton = document.getElementById("uploadButton");
const dropZone = document.getElementById("dropZone");
const fileName = document.getElementById("fileName");
const statusText = document.getElementById("statusText");

let selectedFile = null;

const setStatus = (message, isError = false) => {
    statusText.textContent = message;
    statusText.style.color = isError ? "#f87171" : "var(--muted)";
};

const updateSelectedFile = (file) => {
    selectedFile = file;
    fileName.textContent = file ? file.name : "No file selected";
    uploadButton.disabled = !file;
};

selectButton.addEventListener("click", (event) => {
    event.stopPropagation(); // prevent dropzone click handler from firing twice
    fileInput.click();
});

fileInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    updateSelectedFile(file);
    setStatus("");
});

const handleDrop = (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-dragging");
    const [file] = event.dataTransfer.files || [];
    if (!file) return;
    updateSelectedFile(file);
    setStatus("");
};

dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("is-dragging");
});

dropZone.addEventListener("dragleave", () => dropZone.classList.remove("is-dragging"));
dropZone.addEventListener("drop", handleDrop);

const uploadImage = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile, selectedFile.name);

    setStatus("Uploading...");
    uploadButton.disabled = true;

    try {
        const response = await fetch(`${apiBase}/images`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || "Upload failed");
        }

        const payload = await response.json();
        if (!payload.id) {
            throw new Error("Missing image id in response");
        }

        window.location.href = `/${encodeURIComponent(payload.id)}`;
    } catch (err) {
        console.error(err);
        setStatus(err.message || "Could not upload the file", true);
        uploadButton.disabled = false;
    }
};

uploadButton.addEventListener("click", uploadImage);

// Keyboard accessibility for dropzone click
dropZone.addEventListener("click", (event) => {
    if (event.target === selectButton) return;
    fileInput.click();
});
