// ゲーム概要ページ (docs/game-overview.md) の動き
// - [data-ms-typewriter]: 画面に入ったら一文字ずつ表示する
// - [data-ms-area]: 区域選択画面のように ◀ ▶ でエリアを切り替える
(function () {
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches

  document.querySelectorAll("[data-ms-typewriter]").forEach(function (el) {
    if (reduced || !("IntersectionObserver" in window)) return
    var text = el.textContent
    el.setAttribute("aria-label", text)
    el.textContent = ""
    el.classList.add("is-typing")
    var io = new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) return
      io.disconnect()
      var i = 0
      var timer = setInterval(function () {
        el.textContent = text.slice(0, ++i)
        if (i >= text.length) {
          clearInterval(timer)
          el.classList.remove("is-typing")
        }
      }, 45)
    })
    io.observe(el)
  })

  document.querySelectorAll("[data-ms-area]").forEach(function (root) {
    var items = Array.prototype.slice.call(root.querySelectorAll(".ms-area__item"))
    if (items.length < 2) return
    var current = 0
    root.classList.add("is-carousel")
    root.setAttribute("tabindex", "0")
    root.setAttribute("aria-roledescription", "carousel")

    function button(label, cls, step) {
      var b = document.createElement("button")
      b.type = "button"
      b.className = "ms-area__nav " + cls
      b.setAttribute("aria-label", label)
      b.addEventListener("click", function () { show(current + step) })
      return b
    }
    items.forEach(function (item) {
      var name = item.querySelector(".ms-area__name")
      name.insertBefore(button("前のエリア", "ms-area__nav--prev", -1), name.firstChild)
      name.appendChild(button("次のエリア", "ms-area__nav--next", 1))
    })
    var counter = document.createElement("p")
    counter.className = "ms-area__count"
    root.appendChild(counter)

    function show(n) {
      current = (n + items.length) % items.length
      items.forEach(function (item, i) { item.hidden = i !== current })
      counter.textContent = (current + 1) + " / " + items.length
    }
    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") show(current - 1)
      if (e.key === "ArrowRight") show(current + 1)
    })
    show(0)
  })
})()

