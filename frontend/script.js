// Кварта — поведение страницы.
// 1) плавное появление секций при прокрутке (только если анимации разрешены);
// 2) подстановка типа обращения и названия товара при клике на «Заказать» / «Оформить»;
// 3) честное сообщение, что форма пока ничего не отправляет.

(function () {
  'use strict';

  // 1. Появление секций ------------------------------------------------------
  var prefersReducedMotion =
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!prefersReducedMotion && 'IntersectionObserver' in window) {
    document.documentElement.classList.add('js');

    var observer = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -5% 0px' }
    );

    document.querySelectorAll('.reveal').forEach(function (el) {
      observer.observe(el);
    });
  }

  // 2 и 3. Форма --------------------------------------------------------------
  var form = document.getElementById('request-form');
  var status = document.getElementById('form-status');
  var typeSelect = document.getElementById('field-type');
  var comment = document.getElementById('field-comment');

  if (!form || !status || !typeSelect || !comment) {
    return;
  }

  // Текст, который мы сами подставили в комментарий: его можно заменять,
  // а то, что человек написал сам, — нельзя.
  var autoText = '';

  document.querySelectorAll('[data-request-type]').forEach(function (link) {
    link.addEventListener('click', function () {
      typeSelect.value = link.getAttribute('data-request-type');
      status.textContent = '';

      var product = link.getAttribute('data-product');
      var canReplace = comment.value.trim() === '' || comment.value === autoText;

      if (canReplace) {
        autoText = product ? 'Хочу заказать: ' + product : '';
        comment.value = autoText;
      }
    });
  });

  
  // Отправка заявки в FastAPI
  var API_URL = 'http://127.0.0.1:8000/api/lead';
  var submitButton = form.querySelector('button[type="submit"]');

  form.addEventListener('submit', async function (event) {
    event.preventDefault();

    if (!form.reportValidity()) {
      return;
    }

    var originalButtonText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Отправляем...';
    status.textContent = '';

    var formData = new FormData(form);
    var params = new URLSearchParams(window.location.search);

    // Преобразуем значения HTML-формы в значения API
    var typeMap = {
      coffee: 'one_off',
      drip: 'one_off',
      subscription: 'subscription',
      other: 'question'
    };

    var payload = {
      name: formData.get('name').trim(),
      phone: formData.get('phone').trim(),
      interest: typeMap[formData.get('type')],
      comment: formData.get('comment').trim() || null,

      // Рекламные параметры из адресной строки
      utm_source: params.get('utm_source'),
      utm_campaign: params.get('utm_campaign'),
      utm_content: params.get('utm_content'),
      landing_page: window.location.pathname
    };

    try {
      var response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      var result = await response.json();

      if (!response.ok) {
        var errorMessage = Array.isArray(result.detail)
          ? result.detail.map(function (error) {
              return error.msg;
            }).join('. ')
          : typeof result.detail === 'string'
            ? result.detail
            : 'Проверьте данные и попробуйте ещё раз.';

        throw new Error(errorMessage);
      }

      status.textContent =
        'Заявка принята! Спасибо, мы свяжемся с вами.';

      form.reset();
      autoText = '';

    } catch (error) {
      status.textContent = error instanceof TypeError
        ? 'Не удалось связаться с сервером. Проверьте подключение и попробуйте ещё раз.'
        : error.message;
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = originalButtonText;
    }
  });

  form.addEventListener('input', function () {
    status.textContent = '';
  });


  form.addEventListener('input', function () {
    status.textContent = '';
  });
})();