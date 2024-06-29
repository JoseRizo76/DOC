document.addEventListener("DOMContentLoaded", function() {
    var errorElement = document.querySelector("#error");
    if (errorElement) {
        setTimeout(function() {
            errorElement.style.display = 'none';
        }, 2000);
    }
});
