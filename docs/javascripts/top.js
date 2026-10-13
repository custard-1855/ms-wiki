// トップページ (docs/index.md) の演出
// - ロゴ: 初回だけ書く演出。2 回目以降 (同じタブ) はすぐ出す
// - マナオーブ: canvas に光の粒を漂わせ、カーソルに吸い寄せる
// - カード: ギザギザの枠を描く SVG を差し込む (描く動きは CSS)
// 魔法の絵が滲み出る背景は CSS だけで動く
;(function () {
  var top = document.querySelector("[data-ms-top]")
  if (!top) return
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches

  try {
    if (sessionStorage.getItem("ms-top-seen")) top.classList.add("is-instant")
    sessionStorage.setItem("ms-top-seen", "1")
  } catch (e) {}

  // カード: 枠の SVG を差し込む
  var cards = document.querySelectorAll(".ms-cards > ul > li")
  cards.forEach(function (li) {
    li.classList.add("ms-card")
    var ns = "http://www.w3.org/2000/svg"
    var svg = document.createElementNS(ns, "svg")
    svg.setAttribute("class", "ms-card__frame")
    svg.setAttribute("aria-hidden", "true")
    var rect = document.createElementNS(ns, "rect")
    rect.setAttribute("x", "0")
    rect.setAttribute("y", "0")
    rect.setAttribute("width", "100%")
    rect.setAttribute("height", "100%")
    rect.setAttribute("pathLength", "1")
    svg.appendChild(rect)
    li.appendChild(svg)
  })

  if (reduced) return

  // マナオーブ (色はゲームのマナオーブの小・中・大から)
  var canvas = top.querySelector(".ms-top__orbs")
  var ctx = canvas.getContext("2d")
  var colors = ["63,216,208", "255,165,58", "224,92,255"]
  var sprites = colors.map(function (rgb) {
    var c = document.createElement("canvas")
    c.width = c.height = 64
    var g = c.getContext("2d")
    var grad = g.createRadialGradient(32, 32, 0, 32, 32, 32)
    grad.addColorStop(0, "rgba(255,255,255,0.95)")
    grad.addColorStop(0.18, "rgba(" + rgb + ",0.9)")
    grad.addColorStop(0.45, "rgba(" + rgb + ",0.25)")
    grad.addColorStop(1, "rgba(" + rgb + ",0)")
    g.fillStyle = grad
    g.fillRect(0, 0, 64, 64)
    return c
  })
  var dpr = Math.min(window.devicePixelRatio || 1, 2)
  var w = 0, h = 0, orbs = [], pointer = null, running = false, visible = true

  function resize() {
    w = top.clientWidth
    h = top.clientHeight
    canvas.width = w * dpr
    canvas.height = h * dpr
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
  function spawn(o, anywhere) {
    o.x = Math.random() * w
    o.y = anywhere ? Math.random() * h : h + 10
    o.r = 6 + Math.random() * 10
    o.vy = 0.15 + Math.random() * 0.35
    o.phase = Math.random() * Math.PI * 2
    o.sprite = sprites[(Math.random() * sprites.length) | 0]
    o.alpha = 0.35 + Math.random() * 0.45
    return o
  }
  resize()
  var count = w < 600 ? 16 : 34
  for (var i = 0; i < count; i++) orbs.push(spawn({}, true))

  function step(t) {
    if (!running) return
    ctx.clearRect(0, 0, w, h)
    ctx.globalCompositeOperation = "lighter"
    orbs.forEach(function (o) {
      o.y -= o.vy
      o.x += Math.sin(t / 2400 + o.phase) * 0.18
      if (pointer) {
        var dx = pointer.x - o.x, dy = pointer.y - o.y
        var d = Math.sqrt(dx * dx + dy * dy)
        if (d < 140) {
          var pull = (1 - d / 140) * 2.2
          o.x += (dx / d) * pull
          o.y += (dy / d) * pull
          if (d < 8) spawn(o, false)
        }
      }
      if (o.y < -20) spawn(o, false)
      ctx.globalAlpha = o.alpha
      ctx.drawImage(o.sprite, o.x - o.r, o.y - o.r, o.r * 2, o.r * 2)
    })
    ctx.globalAlpha = 1
    requestAnimationFrame(step)
  }
  function update() {
    var should = visible && !document.hidden
    if (should && !running) { running = true; requestAnimationFrame(step) }
    if (!should) running = false
  }
  top.addEventListener("pointermove", function (e) {
    var r = top.getBoundingClientRect()
    pointer = { x: e.clientX - r.left, y: e.clientY - r.top }
  })
  top.addEventListener("pointerleave", function () { pointer = null })
  window.addEventListener("resize", resize)
  document.addEventListener("visibilitychange", update)
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting
      update()
    }).observe(top)
  }
  update()
})()
