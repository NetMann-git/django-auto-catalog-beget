(function () {
    function initAccordion(root) {
        var panels = Array.prototype.slice.call(root.querySelectorAll('.home-inspection__panel'));

        function setOpen(panel, open) {
            var button = panel.querySelector('.home-inspection__panel-heading');
            var collapse = panel.querySelector('.home-inspection__panel-collapse');
            if (!button || !collapse) return;

            panel.classList.toggle('is-active', open);
            button.setAttribute('aria-expanded', open ? 'true' : 'false');
            collapse.hidden = !open;
        }

        panels.forEach(function (panel) {
            var button = panel.querySelector('.home-inspection__panel-heading');
            if (!button) return;

            button.addEventListener('click', function () {
                var wasOpen = button.getAttribute('aria-expanded') === 'true';

                panels.forEach(function (item) {
                    if (item !== panel) setOpen(item, false);
                });

                setOpen(panel, !wasOpen);
            });
        });
    }

    function initTabs(root) {
        var buttons = Array.prototype.slice.call(root.querySelectorAll('[data-tab-target]'));
        if (!buttons.length) {
            return;
        }

        function activate(button) {
            var targetId = button.getAttribute('data-tab-target');

            buttons.forEach(function (item) {
                var isActive = item === button;
                var panelId = item.getAttribute('data-tab-target');
                var panel = root.querySelector('#' + panelId);

                item.classList.toggle('is-active', isActive);
                item.setAttribute('aria-selected', isActive ? 'true' : 'false');
                item.tabIndex = isActive ? 0 : -1;

                if (panel) {
                    panel.hidden = !isActive;
                    panel.classList.toggle('is-active', isActive);
                }
            });

            var target = root.querySelector('#' + targetId);
            if (target) {
                target.hidden = false;
            }
        }

        buttons.forEach(function (button, index) {
            button.addEventListener('click', function () {
                activate(button);
            });

            button.addEventListener('keydown', function (event) {
                if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') {
                    return;
                }

                event.preventDefault();
                var direction = event.key === 'ArrowRight' ? 1 : -1;
                var nextIndex = (index + direction + buttons.length) % buttons.length;
                buttons[nextIndex].focus();
                activate(buttons[nextIndex]);
            });
        });
    }

    document.querySelectorAll('[data-inspection-accordion]').forEach(initAccordion);
    document.querySelectorAll('[data-home-tabs]').forEach(initTabs);
})();
