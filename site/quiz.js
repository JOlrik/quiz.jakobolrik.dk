// Quizmotor: et spørgsmål ad gangen, pointene lægges sammen pr. resultat,
// og det resultat med flest point vinder (samme regel som den gamle platform).
(function () {
  var data = JSON.parse(document.getElementById('quiz-data').textContent);
  var intro = document.getElementById('intro');
  var spm = document.getElementById('spm');
  var titel = document.getElementById('spm-titel');
  var beskrivelse = document.getElementById('spm-beskrivelse');
  var liste = document.getElementById('spm-svar');
  var taeller = document.getElementById('spm-taeller');
  var bar = document.getElementById('spm-bar');
  var tilbage = document.getElementById('spm-tilbage');

  var valg = [];
  var nr = 0;

  function vis(i) {
    nr = i;
    var q = data.spoergsmaal[i];
    titel.textContent = q.titel;
    beskrivelse.textContent = q.beskrivelse || '';
    beskrivelse.classList.toggle('skjult', !q.beskrivelse);
    taeller.textContent = 'Spørgsmål ' + (i + 1) + ' af ' + data.spoergsmaal.length;
    bar.style.width = (i / data.spoergsmaal.length * 100) + '%';
    tilbage.classList.toggle('skjult', i === 0);
    liste.innerHTML = '';
    q.svar.forEach(function (s, j) {
      var li = document.createElement('li');
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = s.titel;
      if (valg[i] === j) b.className = 'valgt';
      b.addEventListener('click', function () { vaelg(j, b); });
      li.appendChild(b);
      liste.appendChild(li);
    });
    window.scrollTo(0, 0);
    var foerste = liste.querySelector('button');
    if (foerste) foerste.focus({ preventScroll: true });
  }

  function vaelg(j, knap) {
    valg[nr] = j;
    valg.length = nr + 1;
    knap.className = 'valgt';
    setTimeout(function () {
      if (nr + 1 < data.spoergsmaal.length) vis(nr + 1);
      else afslut();
    }, 180);
  }

  function afslut() {
    bar.style.width = '100%';
    var point = {};
    data.resultater.forEach(function (r) { point[r.id] = 0; });
    valg.forEach(function (j, i) {
      var p = data.spoergsmaal[i].svar[j].point;
      for (var rid in p) if (rid in point) point[rid] += p[rid];
    });
    // Ved lige point vinder det første resultat i rækkefølgen.
    var vinder = data.resultater[0];
    data.resultater.forEach(function (r) { if (point[r.id] > point[vinder.id]) vinder = r; });
    location.href = vinder.slug + '/?mit=1';
  }

  document.getElementById('start').addEventListener('click', function () {
    intro.classList.add('skjult');
    spm.classList.remove('skjult');
    vis(0);
  });
  tilbage.addEventListener('click', function () { if (nr > 0) vis(nr - 1); });
})();
