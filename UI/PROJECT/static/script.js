let mediaRecorder;
let audioChunks = [];
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(sendLocationToServer, showError);
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

let recognition;

function startVoiceActivation() {
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
        const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
        console.log('Transcript:', transcript);  // Debugging output

        if (transcript.includes('activate shield')) { // Your custom wake word
            if (!document.getElementById('listenToggle').checked) {
                document.getElementById('listenToggle').click(); // Toggle on
            }
        }

        if (transcript.includes('stop recording')) {  // Custom stop recording command
            if (mediaRecorder && mediaRecorder.state === "recording") {
                stopRecording().then(() => { // Ensure stopRecording finishes before toggling button
                    document.getElementById("status").innerText = "Recording stopped.";
                    document.getElementById("status").style.color = "#ff6f91";
                    
                    // Toggle the button state
                    document.getElementById('listenToggle').click();
                });
            }
        }
    };

    recognition.onend = () => {
        // Automatically restart recognition if it ends
        if (isListening) {
            recognition.start();
        }
    };

    recognition.start();
    isListening = true;
}
// Start listening on page load
document.addEventListener('DOMContentLoaded', () => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        document.getElementById('voice-status').style.display = 'block';
        startVoiceActivation();
    } else {
        console.log("Speech recognition not supported");
    }
});
function sendLocationToServer(position) {
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;
    console.log(latitude,longitude)
    // Send location to Flask backend
    fetch('http://127.0.0.1:5000/send-location', {  // Adjust the URL if necessary
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ latitude: latitude, longitude: longitude })
    })
    .then(response => {
        if (response.status === 401) {
            console.error("User not logged in!");
            alert("You must be logged in to send location.");
            return;
        }
        return response.json();
    })
    .then(data => {
        console.log('Location sent successfully:', data);


    })
    .catch(error => {
        console.error('Error sending location:', error);
    });
}

function showError(error) {
    console.log("Geolocation error:", error);  // Add this for debugging
    switch(error.code) {
        case error.PERMISSION_DENIED:
            alert("User denied the request for Geolocation.");
            break;
        case error.POSITION_UNAVAILABLE:
            alert("Location information is unavailable.");
            break;
        case error.TIMEOUT:
            alert("The request to get user location timed out.");
            break;
        case error.UNKNOWN_ERROR:
            alert("An unknown error occurred.");
            break;
    }
}
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("listenToggle");
    const statusText = document.getElementById("status");

    toggle.addEventListener("change", async function() {
        if (this.checked) {
            startRecording();
            statusText.innerText = "Recording started...";
            document.getElementById("status").style.color = "#ff6f91";

        } else {
            stopRecording();
            statusText.innerText = "Processing your audio. Please wait for a while...";
            document.getElementById("status").style.color = "#ff6f91";

        }
    });
});

async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };
}

async function stopRecording() {
    mediaRecorder.stop();
    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.wav");

        // Send audio to Flask backend
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        console.log(result);
        if (result.message.toLowerCase().includes("fearful")) {
            document.getElementById("status").innerText = "⚠️ Fear Detected!";
            document.getElementById("status").style.color = "red"; 
            getLocation();
              // Show the popup
              const popup = document.getElementById("popup");
              popup.classList.add("show"); // Make the popup visible
              console.log("Fear detected, showing popup.");  // Debugging log
  
              setTimeout(() => {
                  popup.classList.add("hide"); // Hide after 15 seconds
                  setTimeout(() => {
                      popup.classList.remove("show", "hide"); // Reset the popup
                  }, 1200); // Match slideOut animation duration
              }, 15000); // Popup display time
        } else {
            document.getElementById("status").innerText = "✅ No Fear Detected";
            document.getElementById("status").style.color = "green"; 
        }

        // Reset chunks for next recording
        audioChunks = [];
    };
}