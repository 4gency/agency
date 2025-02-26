window._emojiSettings = {
  baseUrl: "https://s.w.org/images/core/emoji/15.0.3/72x72/",
  ext: ".png",
  svgUrl: "https://s.w.org/images/core/emoji/15.0.3/svg/",
  svgExt: ".svg",
  source: { concatemoji: "/js/emoji-release.min.js?ver=6.6.2" },
}
/*! This file is auto-generated */
!((i, n) => {
  let o
  let s
  let e
  function c(e) {
    try {
      const t = { supportTests: e, timestamp: new Date().valueOf() }
      sessionStorage.setItem(o, JSON.stringify(t))
    } catch (e) {}
  }
  function p(e, t, n) {
    e.clearRect(0, 0, e.canvas.width, e.canvas.height), e.fillText(t, 0, 0)
    const t = new Uint32Array(
      e.getImageData(0, 0, e.canvas.width, e.canvas.height).data,
    )
    const r =
      (e.clearRect(0, 0, e.canvas.width, e.canvas.height),
      e.fillText(n, 0, 0),
      new Uint32Array(
        e.getImageData(0, 0, e.canvas.width, e.canvas.height).data,
      ))
    return t.every((e, t) => e === r[t])
  }
  function u(e, t, n) {
    switch (t) {
      case "flag":
        return n(e, "🏳️‍⚧️", "🏳️​⚧️") ? !1 : !n(e, "🇺🇳", "🇺​🇳") && !n(e, "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "🏴​󠁧​󠁢​󠁥​󠁮​󠁧​󠁿")
      case "emoji":
        return !n(e, "🐦‍⬛", "🐦​⬛")
    }
    return !1
  }
  function f(e, t, n) {
    const r =
      "undefined" !== typeof WorkerGlobalScope &&
      self instanceof WorkerGlobalScope
        ? new OffscreenCanvas(300, 150)
        : i.createElement("canvas")
    const a = r.getContext("2d", { willReadFrequently: !0 })
    const o = ((a.textBaseline = "top"), (a.font = "600 32px Arial"), {})
    return (
      e.forEach((e) => {
        o[e] = t(a, e, n)
      }),
      o
    )
  }
  function t(e) {
    const t = i.createElement("script")
    ;(t.src = e), (t.defer = !0), i.head.appendChild(t)
  }
  "undefined" !== typeof Promise &&
    ((o = "emojiSettingsSupports"),
    (s = ["flag", "emoji"]),
    (n.supports = { everything: !0, everythingExceptFlag: !0 }),
    (e = new Promise((e) => {
      i.addEventListener("DOMContentLoaded", e, { once: !0 })
    })),
    new Promise((t) => {
      let n = (() => {
        try {
          const e = JSON.parse(sessionStorage.getItem(o))
          if (
            "object" === typeof e &&
            "number" === typeof e.timestamp &&
            new Date().valueOf() < e.timestamp + 604800 &&
            "object" === typeof e.supportTests
          )
            return e.supportTests
        } catch (e) {}
        return null
      })()
      if (!n) {
        if (
          "undefined" !== typeof Worker &&
          "undefined" !== typeof OffscreenCanvas &&
          "undefined" !== typeof URL &&
          URL.createObjectURL &&
          "undefined" !== typeof Blob
        )
          try {
            const e = `postMessage(${f.toString()}(${[
              JSON.stringify(s),
              u.toString(),
              p.toString(),
            ].join(",")}));`
            const r = new Blob([e], { type: "text/javascript" })
            const a = new Worker(URL.createObjectURL(r), {
              name: "TestEmojiSupports",
            })
            return void (a.onmessage = (e) => {
              c((n = e.data)), a.terminate(), t(n)
            })
          } catch (e) {}
        c((n = f(s, u, p)))
      }
      t(n)
    })
      .then((e) => {
        for (const t in e)
          (n.supports[t] = e[t]),
            (n.supports.everything = n.supports.everything && n.supports[t]),
            "flag" !== t &&
              (n.supports.everythingExceptFlag =
                n.supports.everythingExceptFlag && n.supports[t])
        ;(n.supports.everythingExceptFlag =
          n.supports.everythingExceptFlag && !n.supports.flag),
          (n.DOMReady = !1),
          (n.readyCallback = () => {
            n.DOMReady = !0
          })
      })
      .then(() => e)
      .then(() => {
        let e
        n.supports.everything ||
          (n.readyCallback(),
          (e = n.source || {}).concatemoji
            ? t(e.concatemoji)
            : e.emoji && e.twemoji && (t(e.twemoji), t(e.emoji)))
      }))
})((window, document), window._emojiSettings)
