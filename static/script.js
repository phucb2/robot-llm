
function handleDirection(direction) {
    console.log(direction + ' button pressed');
    // Enable the button after the response is received from the server
    fetch('/cmd/move?direction=' + direction + '&speed=100', {
        method: 'POST'
    }).then(response => {
        console.log('Response:', response);
    }).catch(error => {
        console.error('Error:', error);
    })
}

function handleFlash(status) {
    console.log('Flash button pressed');
    // Map true/false to on/off
    status = status ? 'on' : 'off';
    fetch('/cmd/flashlight?status=' + status, {
        method: 'POST'
    }).then(response => {
        console.log('Response:', response);
    }).catch(error => {
        console.error('Error:', error);
    })
}

// On loaded
document.addEventListener('DOMContentLoaded', () => {
    // Handle hover and release events
    document.getElementById('forward').addEventListener('mousedown', () => {
        handleDirection('F');
    });
    document.getElementById('forward').addEventListener('mouseup', () => {
        handleDirection('S');
    });
    
    // Handle hover and release events for left button
    document.getElementById('left').addEventListener('mousedown', () => {
        handleDirection('L');
    });
    document.getElementById('left').addEventListener('mouseup', () => {
        handleDirection('S');
    });

    // Handle hover and release events for right button
    document.getElementById('right').addEventListener('mousedown', () => {
        handleDirection('R');
    });
    document.getElementById('right').addEventListener('mouseup', () => {
        handleDirection('S');
    });
    // Handle hover and release events for down button
    document.getElementById('backward').addEventListener('mousedown', () => {
        handleDirection('B');
    });
    document.getElementById('backward').addEventListener('mouseup', () => {
        handleDirection('S');
    });

    // handle input toggle flashToggle
    document.getElementById('flashToggle').addEventListener('change', () => {
        console.log('Flash toggle changed');
        handleFlash(document.getElementById('flashToggle').checked);
    });
});