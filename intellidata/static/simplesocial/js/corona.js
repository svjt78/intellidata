console.clear();

const PI = Math.PI;
const PI2 = PI * 2;
const PI180 = PI / 180;

const cvs1 = document.getElementById("canvas");
const cvs2 = document.getElementById("orbits");
const ctx1 = cvs1.getContext("2d");
const ctx2 = cvs2.getContext("2d");

const di = Math.max(window.innerWidth, window.innerHeight) * 2;
cvs1.height = cvs2.height = di;
cvs1.width = cvs2.width = di;

ctx1.fillRect(0, 0, cvs1.width, cvs1.height);

document.body.style.setProperty("--di", cvs1.width * 0.5);

class Vector {
  constructor(rat, cx, cy, rate, reverse) {
    this.x = cx * rat;
    this.y = cy;
    this.cx = cx;
    this.cy = cy;
    const radians = PI180 * rate;
    this.cos = Math.cos(reverse ? radians * -1 : radians);
    this.sin = Math.sin(reverse ? radians * -1 : radians);
  }

  tick() {
    const x = this.x - this.cx;
    const y = this.y - this.cy;
    this.x = (this.cos * x) + (this.sin * y) + this.cx;
    this.y = (this.cos * y) - (this.sin * x) + this.cy;
  }
}

const cx = cvs1.width * 0.5;
const cy = cvs1.height * 0.5;

const items = 5;
const vectors = [];
for (var i = 0; i < items; i++)
  vectors.push(new Vector(Math.random(), cx, cy, Math.random() * 5 + 1, i % 2 === 0));

let paused = false;
let tick = 0;

document.body.addEventListener("click", () => {
  paused = !paused;
  if (!paused) tick = 0;
  cvs2.style.display = paused ? "none" : "block";
});


animate();

function animate() {
  requestAnimationFrame(animate);

  if (paused) return;

  ctx1.strokeStyle = "rgba(255, 255, 255, 0.4)";
  ctx2.clearRect(0, 0, cvs2.width, cvs2.height);
  ctx2.fillStyle = "white";

  ctx1.beginPath();

  vectors.forEach((vector, i) => {
    if (i === 0) ctx1.moveTo(vector.x, vector.y);
    else if (i > 1) ctx1.quadraticCurveTo(vectors[i - 1].x, vectors[i - 1].y, vector.x, vector.y);

    ctx2.beginPath();
    ctx2.arc(vector.x, vector.y, 5, 0, PI2);
    ctx2.fill();

    vector.tick();
  });

  ctx1.stroke();

  tick ++;
  if (tick >= 300) paused = true;
}
