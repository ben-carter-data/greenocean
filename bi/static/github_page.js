
if (!window.ghPageCopyReady) {
    window.ghPageCopyReady = true;
    document.addEventListener("click", (event) => {
        const button = event.target.closest(".gh-copy");
        if (!button) { return; }
        const url = button.getAttribute("data-copy");
        const done = () => {
            button.classList.add("is-copied");
            button.setAttribute("title", "Copiado");
            clearTimeout(button.ghTimer);
            button.ghTimer = setTimeout(() => {
                button.classList.remove("is-copied");
                button.setAttribute("title", "Copiar enlace");
            }, 1500);
        };
        const copyWithField = () => {
            const field = document.createElement("textarea");
            field.value = url;
            field.style.position = "fixed";
            field.style.opacity = "0";
            document.body.appendChild(field);
            field.select();
            const copied = document.execCommand("copy");
            field.remove();
            if (copied) { done(); }
        };
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(done, copyWithField);
        } else {
            copyWithField();
        }
    });
}
