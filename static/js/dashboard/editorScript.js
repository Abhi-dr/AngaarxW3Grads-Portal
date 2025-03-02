

    $(document).ready(function () {
        const editor = ace.edit("editor");
        const languageSelect = $("#language");


        // Define top languages (example)
        const topLanguages = [
            {
                id: 71,
                name: "Python"
            }, {
                id: 62,
                name: "Java"
            }, {
                id: 50,
                name: "C"
            }, {
                id: 54,
                name: "C++"
            },];



        // Default code snippets for specific languages
        const defaultCode = {
            71: `{{ question.driver_code|safe    }}`, // Python default
            50: `#include <stdio.h>\n\nint main() {\n\t// Write your C code here\n\treturn 0;\n}`, // C default
            54: `#include <iostream>\nusing namespace std;\n\nint main() {\n\t// Write your C++ code here\n\treturn 0;\n}`, // C++ default
            62: `` // Java default
            // Add more language defaults as needed
        };

        // Function to set editor content based on selected language
        function setEditorContent(languageId) {
            if (defaultCode[languageId]) {
                editor.setValue(defaultCode[languageId], -1); // Set default code
            } else {
                editor.setValue(`{{ question.driver_code|safe    }}`, -1); // Fallback default
            }
        }

        // Fetch languages from API
        topLanguages.forEach(function (language) {
            languageSelect.append(
                `<option value="${language.id}">${language.name}</option>`
            );
        });

        const initialLanguageId = languageSelect.val();
        setEditorContent(initialLanguageId);


        // Trigger when the language is changed
        languageSelect.change(function () {
            let selectedLanguageId = $(this).val();
            setEditorContent(selectedLanguageId); // Set the default code for the selected language

            // reset the output div
            $("#output").addClass("d-none");
            $("#output pre").text("");

        });

    });


    $(document).ready(function () {

        const editor = ace.edit("editor");

        // change the theme of ace editor based on selected theme of the website
        let theme = localStorage.getItem("theme");
        if (theme == "dark") {
            editor.setTheme("ace/theme/twilight");
        } else {
            editor.setTheme("ace/theme/chrome");
        }

        // editor.setTheme("ace/theme/twilight");

        // get selected language and set editor mode
        let selectedLanguage = $("#language").val();


        editor.session.setMode("ace/mode/python");
        editor.setOptions({
            //enableBasicAutocompletion: true,
            enableSnippets: true,
            //enableLiveAutocompletion: true,
            cursorStyle: "smooth",
            //enableEmmet: true,
        });

        // change the editor mode based on selected language
        $("#language").change(function () {
            let selectedLanguage = $(this).val();
            if (selectedLanguage == 71) {
                editor.session.setMode("ace/mode/python");
            } else if (selectedLanguage == 50) {
                editor.session.setMode("ace/mode/c_cpp");
            } else if (selectedLanguage == 54) {
                editor.session.setMode("ace/mode/c_cpp");
            } else if (selectedLanguage == 62) {
                editor.session.setMode("ace/mode/java");
            }
        });


    });


    $(document).keydown(function (event) {
        // Check if Ctrl + Enter is pressed
        if (event.ctrlKey && event.key === "Enter") {
            event.preventDefault();
            console.log("Ctrl+Enter is pressed"); // For debugging
            $("#submit-btn").click(); // Trigger the submit button
            const testCaseResultsDiv = document.getElementById('testCaseResults');

            while (testCaseResultsDiv.firstChild) {
                testCaseResultsDiv.removeChild(testCaseResultsDiv.firstChild);
            };


            document.getElementById("testCaseResults").scrollIntoView({
                behavior: 'smooth'
            });
        }

        // check if Alt + Enter is pressed
        if (event.altKey && event.key === "Enter") {
            event.preventDefault();
            console.log("Alt + Enter is pressed"); // For debugging
            $("#run-btn").click(); // Trigger the run button
        }
    });



    document.getElementById('codeSubmissionForm').addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent default form submission

        const editor = ace.edit('editor');

        const submit_btn = $("#submit-btn");

        submit_btn.prop("disabled", true);

        let countdown = 10;
        submit_btn.text(`Submitting... (Wait for ${countdown} seconds)`);

        const countdownInterval = setInterval(() => {
            countdown -= 1;
            submit_btn.text(`Submitting... (Wait for ${countdown} seconds)`);
            if (countdown <= 0) {
                clearInterval(countdownInterval);
            }
        }, 1500);


        let code = editor.getValue();

        if (!code.trim()) {
            alert("Code cannot be empty!");
            event.preventDefault(); // Prevent form submission
        }

        document.getElementById('submission_code').value = code;

        const formData = new FormData(this);

        fetch("{% url 'submit_code' question.slug %}", {
            method: 'POST',
            body: formData,
        })
            .then(response => response.json())
            .then(data => {
                console.log("TOKEN: ", data.token);
                const testCaseResultsDiv = document.getElementById('testCaseResults');
                testCaseResultsDiv.innerHTML = ''; // Clear previous results

                clearInterval(countdownInterval); // Clear the interval
                submit_btn.prop("disabled", false);
                submit_btn.text("Submit Code");

                testCaseResultsDiv.scrollIntoView({
                    behavior: 'smooth'
                });

                // If there are test case results, display them
                if (data.test_case_results) {
                    data.test_case_results.forEach((result, index) => {
                        const resultDiv = document.createElement('div');
                        resultDiv.classList.add(
                            'card',
                            'mb-3',
                            'test-case-result',
                            result.status === "Passed" ? 'border-success' : 'border-danger',
                            'shadow-sm'
                        );

                        resultDiv.id = "test-case-result-id";

                        // Include compiler output only when the test case fails
                        const compilerOutputHTML = document.createElement('div');
                        compilerOutputHTML.id = "compiler-output";
                        if (result.compiler_output) {
                            compilerOutputHTML += `
                                <p><strong>Compiler Output:</strong></p>
                                <pre class="p-2 rounded bg-warning text-dark">${result.compiler_output}</pre>
                            `;

                            document.getElementById("compiler-output").scrollIntoView({ behavior: 'smooth' });
                        }

                        resultDiv.innerHTML = `
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <span>
                                    <strong>Test Case ${index + 1}</strong> - 
                                    <span class="badge 
                                        ${result.status === "Passed" ? 'bg-success' : 'bg-danger'}">
                                        ${result.status}
                                    </span>
                                </span>
                                <button 
                                    class="btn btn-sm btn-outline-primary toggle-details" 
                                    type="button" 
                                    data-bs-toggle="collapse" 
                                    data-bs-target="#details-${index}" 
                                    aria-expanded="false" 
                                    aria-controls="details-${index}">
                                    Show
                                </button>
                            </div>
                            <div id="details-${index}" class="collapse">
                                <div class="card-body">
                                    <p><strong>Input:</strong></p>
                                    <pre class="p-2 rounded">${result.input}</pre>
                                    <p><strong>Expected Output:</strong></p>
                                    <pre class="p-2 rounded">${result.expected_output}</pre>
                                    <p><strong>Your Output:</strong></p>
                                    <pre class="p-2 rounded">${result.user_output}</pre>
                                    ${compilerOutputHTML}
                                    <p><strong>Status:</strong> 
                                        <span class="badge 
                                            ${result.status === "Passed" ? 'bg-success' : 'bg-danger'}">
                                            ${result.status}
                                        </span>
                                    </p>
                                </div>
                            </div>
                        `;
                        testCaseResultsDiv.appendChild(resultDiv);
                    });


                    if (data.score == 100) {
                        submission_accepted();
                    }
                    document.getElementById("test-case-result-id").scrollIntoView({ behavior: 'smooth' });
                }

                // If there's a global compiler error (e.g., server-side), display it
                if (data.compiler_output) {
                    const globalErrorDiv = document.createElement('div');
                    globalErrorDiv.classList.add('alert', 'alert-danger');
                    globalErrorDiv.innerHTML = `
                        <h5>Compiler Error</h5>
                        <pre>${data.compiler_output}</pre>
                    `;
                    testCaseResultsDiv.prepend(globalErrorDiv);
                }
            })

            .catch(error => {
                console.log('Error:', error);
                // print the token from response                
                console.log("TOKEN: ", error.token);
                clearInterval(countdownInterval); // Clear the interval
                submit_btn.prop("disabled", false);
                submit_btn.text("Submit Code");
            });
    });


    // On successful submission... confetti animation
    function submission_accepted() {
        const start = () => {
            confetti.start();
            setTimeout(function () {
                confetti.stop();
            }, 5000);
        };

        const successModal = new bootstrap.Modal(document.getElementById('next-modal-btn'), {
            keyboard: false
      });

        successModal.show();

        start();

    }

