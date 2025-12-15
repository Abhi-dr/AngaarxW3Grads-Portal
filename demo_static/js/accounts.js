/**
 * accounts.js
 * Handles registration form validation, interactivity, and visual effects.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ===============================================================
    // UTILITIES
    // ===============================================================

    /**
     * Debounce function to limit the rate of function execution.
     * @param {Function} func - The function to debounce.
     * @param {number} wait - The wait time in milliseconds.
     * @returns {Function} - The debounced function.
     */
    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    // ===============================================================
    // STATE MANAGEMENT
    // ===============================================================

    const state = {
        username: false,
        email: false,
        password: false,
        confirmPassword: false
    };

    const elements = {
        usernameInput: document.getElementById('username'),
        emailInput: document.getElementById('email'),
        passwordInput: document.getElementById('password'),
        confirmPasswordInput: document.getElementById('confirm-password'),
        submitBtn: document.getElementById('signup-button'),
        usernameFeedback: document.getElementById('username-feedback'),
        emailFeedback: document.getElementById('email-feedback'),
        passwordMatchError: document.getElementById('password-match'),
        form: document.querySelector('form')
    };

    const urls = {
        checkUsername: elements.form.getAttribute('data-check-username-url'),
        checkEmail: elements.form.getAttribute('data-check-email-url')
    };

    // AbortControllers for cancelling pending requests
    let usernameController = null;
    let emailController = null;

    // ===============================================================
    // VALIDATION LOGIC
    // ===============================================================

    /**
     * Validates Username
     * Constraints: > 4 chars, no spaces, no special chars (alphanumeric only)
     */
    async function checkUsername() {
        const username = elements.usernameInput.value;
        const feedback = elements.usernameFeedback;

        // Reset state
        state.username = false;
        updateSubmitButton();

        // client-side validation
        if (username.length > 0 && username.length < 4) {
            feedback.innerHTML = "<span class='error'>Username must be at least 4 characters</span>";
            return;
        } else if (username.length === 0) {
            feedback.innerHTML = "";
            return;
        }

        const usernameRegex = /^[a-zA-Z0-9]+$/;
        if (!usernameRegex.test(username)) {
            feedback.innerHTML = "<span class='error'>Username must be alphanumeric (no spaces/symbols)</span>";
            return;
        }

        // Server-side check
        if (usernameController) usernameController.abort(); // Cancel previous request
        usernameController = new AbortController();

        try {
            const response = await fetch(`${urls.checkUsername}?username=${encodeURIComponent(username)}`, {
                signal: usernameController.signal
            });
            const data = await response.json();

            if (data.is_available) {
                feedback.innerHTML = "<span class='success'>Username is available</span>";
                state.username = true;
            } else {
                feedback.innerHTML = "<span class='error'>Username is taken</span>";
                state.username = false;
            }
        } catch (error) {
            if (error.name === 'AbortError') return; // Ignore aborted requests
            feedback.innerHTML = "<span class='error'>Error checking availability</span>";
            console.error(error);
        } finally {
            updateSubmitButton();
        }
    }

    /**
     * Validates Email
     */
    async function checkEmail() {
        const email = elements.emailInput.value;
        const feedback = elements.emailFeedback;

        state.email = false;
        updateSubmitButton();

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            if (email.length > 0) feedback.innerHTML = "<span class='error'>Invalid email format</span>";
            else feedback.innerHTML = "";
            return;
        }

        // Server-side check
        if (emailController) emailController.abort();
        emailController = new AbortController();

        try {
            const response = await fetch(`${urls.checkEmail}?email=${encodeURIComponent(email)}`, {
                signal: emailController.signal
            });
            const data = await response.json();

            if (data.is_available) {
                feedback.innerHTML = "<span class='success'>Email is available</span>";
                state.email = true;
            } else {
                feedback.innerHTML = "<span class='error'>Email already registered</span>";
                state.email = false;
            }
        } catch (error) {
            if (error.name === 'AbortError') return;
            feedback.innerHTML = "<span class='error'>Error checking availability</span>";
        } finally {
            updateSubmitButton();
        }
    }

    /**
     * Validates Password Complexity and Match
     */
    function checkPassword() {
        const password = elements.passwordInput.value;
        const confirmPassword = elements.confirmPasswordInput.value;
        const hasStartedTyping = password.length > 0;

        // Requirements
        const reqs = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
        };

        // Update Checklist UI - pass hasStartedTyping to show error state
        updateChecklistUI('req-length', reqs.length, hasStartedTyping);
        updateChecklistUI('req-uppercase', reqs.uppercase, hasStartedTyping);
        updateChecklistUI('req-lowercase', reqs.lowercase, hasStartedTyping);
        updateChecklistUI('req-number', reqs.number, hasStartedTyping);
        updateChecklistUI('req-special', reqs.special, hasStartedTyping);

        const isStrong = Object.values(reqs).every(Boolean);
        state.password = isStrong;

        // Check Match
        if (confirmPassword.length > 0) {
            if (password !== confirmPassword) {
                elements.passwordMatchError.style.display = 'block';
                state.confirmPassword = false;
            } else {
                elements.passwordMatchError.style.display = 'none';
                state.confirmPassword = true;
            }
        } else {
            elements.passwordMatchError.style.display = 'none';
            state.confirmPassword = false;
        }

        updateSubmitButton();
    }

    function updateChecklistUI(id, isValid, hasStartedTyping) {
        const el = document.getElementById(id);
        if (!el) return;

        const icon = el.querySelector('.icon');

        // Remove all state classes first
        el.classList.remove('valid', 'invalid', 'error');

        if (isValid) {
            // Requirement met - green checkmark
            el.classList.add('valid');
            icon.textContent = '✓';
        } else if (hasStartedTyping) {
            // User is typing but requirement not met - red X
            el.classList.add('error');
            icon.textContent = '✗';
        } else {
            // No input yet - neutral state
            el.classList.add('invalid');
            icon.textContent = '○';
        }
    }

    function updateSubmitButton() {
        const isValid = state.username && state.email && state.password && state.confirmPassword;
        elements.submitBtn.disabled = !isValid;
        elements.submitBtn.textContent = isValid ? "Register" : "Register";

        if (!isValid && elements.submitBtn.textContent === "Registering...") {
            // Reset if text was stuck
            elements.submitBtn.textContent = "Register";
        }
    }

    // ===============================================================
    // EVENT LISTENERS
    // ===============================================================

    elements.usernameInput.addEventListener('input', debounce(checkUsername, 300));
    elements.emailInput.addEventListener('input', debounce(checkEmail, 300));
    elements.passwordInput.addEventListener('input', checkPassword);
    elements.confirmPasswordInput.addEventListener('input', checkPassword);

    elements.form.addEventListener('submit', (e) => {
        if (elements.submitBtn.disabled) {
            e.preventDefault();
        } else {
            elements.submitBtn.textContent = "Registering...";
            elements.submitBtn.disabled = true;
        }
    });

    // ===============================================================
    // PASSWORD VISIBILITY TOGGLE
    // ===============================================================

    document.querySelectorAll('.password-toggle').forEach(button => {
        button.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const eyeOpen = this.querySelector('.eye-open');
            const eyeClosed = this.querySelector('.eye-closed');

            if (input.type === 'password') {
                input.type = 'text';
                eyeOpen.style.display = 'none';
                eyeClosed.style.display = 'block';
            } else {
                input.type = 'password';
                eyeOpen.style.display = 'block';
                eyeClosed.style.display = 'none';
            }
        });
    });


    // ===============================================================
    // THREE.JS FIRE IMPLEMENTATION (Moved from inline)
    // ===============================================================
    function initFireAnimation() {
        const canvas = document.getElementById('fire-canvas');
        if (!canvas) return;

        let scene, camera, renderer, fireMesh, clock;

        // Vertex Shader
        const vertexShader = `
            varying vec2 vUv;
            void main() {
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `;

        // Fragment Shader
        const fragmentShader = `
            uniform vec3 color1;
            uniform vec3 color2;
            uniform float time;
            varying vec2 vUv;
            
            float random (vec2 st) {
                return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
            }
            
            float noise (vec2 st) {
                vec2 i = floor(st);
                vec2 f = fract(st);
                float a = random(i);
                float b = random(i + vec2(1.0, 0.0));
                float c = random(i + vec2(0.0, 1.0));
                float d = random(i + vec2(1.0, 1.0));
                vec2 u = f * f * (3.0 - 2.0 * f);
                return mix(a, b, u.x) + (c - a)* u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
            }
            
            float fbm(vec2 st) {
                float value = 0.0;
                float amplitude = 0.5;
                for (int i = 0; i < 6; i++) {
                    value += amplitude * noise(st);
                    st *= 2.0;
                    amplitude *= 0.5;
                }
                return value;
            }
            
            void main() {
                vec2 st = vUv;
                st.y *= 2.0;
                
                float T = time * 0.4;
                vec2 q = vec2(fbm(st + T * 0.01), fbm(st + vec2(1.0)));
                vec2 r = vec2(fbm(st + q * 2.0 + T * 0.1), fbm(st + q * 1.5 + T * 0.05));
                
                float f = fbm(st + r);
                
                float fireShape = 1.0 - smoothstep(0.1, 1.0, st.y);
                f *= fireShape;
                
                vec3 color = mix(color1, color2, clamp((f*f)*4.0, 0.0, 1.0));
                
                gl_FragColor = vec4(color, f * f * f * 2.5);
            }
        `;

        function init3D() {
            scene = new THREE.Scene();
            clock = new THREE.Clock();
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 2.5;
            renderer = new THREE.WebGLRenderer({ canvas, alpha: true });
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.setSize(window.innerWidth, window.innerHeight);

            const fireGeometry = new THREE.PlaneGeometry(10, 5, 32, 32);
            const fireMaterial = new THREE.ShaderMaterial({
                uniforms: {
                    time: { value: 0.0 },
                    color1: { value: new THREE.Color('#ff4f0f') },
                    color2: { value: new THREE.Color('#ff6a00') },
                },
                vertexShader: vertexShader,
                fragmentShader: fragmentShader,
                transparent: true,
                blending: THREE.AdditiveBlending,
                depthWrite: false
            });
            fireMesh = new THREE.Mesh(fireGeometry, fireMaterial);
            scene.add(fireMesh);

            window.addEventListener('resize', onWindowResize);
            document.addEventListener('pointermove', onPointerMove);
            animate();
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }

        function onPointerMove(event) {
            if (fireMesh) {
                const mouseX = (event.clientX / window.innerWidth) * 2 - 1;
                const mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
                camera.rotation.y = (mouseX * 0.1 - camera.rotation.y) * 0.05;
                camera.rotation.x = (mouseY * 0.1 - camera.rotation.x) * 0.05;
            }
        }

        let rafId;
        function animate() {
            const elapsedTime = clock.getElapsedTime();
            fireMesh.material.uniforms.time.value = elapsedTime;
            renderer.render(scene, camera);
            rafId = requestAnimationFrame(animate);
        }

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                cancelAnimationFrame(rafId);
            } else {
                animate();
            }
        });

        init3D();
    }

    initFireAnimation();
});
