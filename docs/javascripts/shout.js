// 叫び (.ms-shout) のアニメーションを、画面に入ったときに始める
(function () {
  if (!("IntersectionObserver" in window)) return
  document.querySelectorAll(".ms-shout").forEach(function (el) {
    el.classList.add("is-pending")
    var io = new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) return
      io.disconnect()
      el.classList.remove("is-pending")
    }, { threshold: 0.6 })
    io.observe(el)
  })
})()
