// 
const router = {
    current: "library",
    routes: {},

    register(name, renderFn) {
        this.routes[name] = renderFn;
    },

    go(name, ...args) {
        this.current = name;
        // Update sidebar
        document.querySelectorAll(".nav-item").forEach(el => {
            el.classList.toggle("active", el.dataset.route === name);
        });
        // Render page
        const fn = this.routes[name];
        if (fn) fn(...args);
    },

    init() {
        // Default page
        this.go("my-learning");
    }
};
