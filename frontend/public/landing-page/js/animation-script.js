document.addEventListener("DOMContentLoaded", () => {
  function playAnimation(element, frame = false) {
    if (frame) {
      element.style.visibility = "visible"
      element.style.opacity = "1"
      element.style.transform = "none"
    }
    if (
      element.getBoundingClientRect().top > 0 &&
      element.getBoundingClientRect().top <= window.innerHeight * 0.75
    ) {
      element.classList.add("lambdagency-animate-init")
    }
  }

  function prepareAnimation(doc, frame = false) {
    const elements = doc.getElementsByClassName("lambdagency-animate")

    for (const element of elements) {
      if (frame) {
        playAnimation(element, true)
      } else {
        window.addEventListener("load", () => {
          playAnimation(element)
        })
        window.addEventListener("scroll", () => {
          playAnimation(element)
        })
      }
    }
  }

  prepareAnimation(document)

  setTimeout(() => {
    const iframe = document.getElementsByClassName(
      "edit-site-visual-editor__editor-canvas",
    )
    const innerDoc =
      iframe.length > 0
        ? iframe[0].contentDocument || iframe[0].contentWindow.document
        : null
    innerDoc ? prepareAnimation(innerDoc, true) : null
  }, 3000)
})
