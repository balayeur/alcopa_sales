document.addEventListener("DOMContentLoaded", function () {
    window.onscroll = function () {
        showScrollButton();
    };

    function showScrollButton() {
        var button = document.getElementById("scrollToTopButton");
        if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
            button.style.display = "block";
        } else {
            button.style.display = "none";
        }
    }

    window.scrollToTop = function () {
        document.body.scrollTop = 0;
        document.documentElement.scrollTop = 0;
    };
});
