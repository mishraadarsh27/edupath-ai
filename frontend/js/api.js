const BASE_URL = "/api";

async function fetchAPI(endpoint, method="GET", body=null) {
    try {
        const options = {
            method,
            headers: { "Content-Type": "application/json" }
        };
        if (body) options.body = JSON.stringify(body);
        
        let coldStartTimer = setTimeout(() => {
            const div = document.createElement("div");
            div.id = "coldStartWarning";
            div.style.cssText = "position:fixed; bottom:20px; right:20px; background:var(--warning, #f39c12); color:white; padding:10px 20px; border-radius:8px; z-index:9999; box-shadow:0 4px 6px rgba(0,0,0,0.1);";
            div.innerHTML = "⏳ Server waking up... please wait (up to 50s).";
            document.body.appendChild(div);
        }, 1500);

        const response = await fetch(`${BASE_URL}${endpoint}`, options);
        
        clearTimeout(coldStartTimer);
        const warning = document.getElementById("coldStartWarning");
        if(warning) warning.remove();

        return await response.json();
    } catch (e) {
        console.error("API Error:", e);
        const warning = document.getElementById("coldStartWarning");
        if(warning) warning.remove();
        return { error: e.message };
    }
}

const api = {
    saveProfile: (data) => fetchAPI("/student/profile", "POST", data),
    getProfile: (id) => fetchAPI(`/student/${id}`, "GET"),
    getUniversities: () => fetchAPI("/universities", "GET"),
    recommendUniversities: (data) => fetchAPI("/universities/recommend", "POST", data),
    calculateROI: (data) => fetchAPI("/roi/calculate", "POST", data),
    predictAdmission: (data) => fetchAPI("/admission/predict", "POST", data),
    chat: (data) => fetchAPI("/chat", "POST", data),
    getChatHistory: (id) => fetchAPI(`/chat/history/${id}`, "GET"),
    calcLoan: (data) => fetchAPI("/loan/calculate", "POST", data),
    applyLoan: (data) => fetchAPI("/loan/apply", "POST", data),
    getReferralStats: (id) => fetchAPI(`/referral/stats/${id}`, "GET"),
    login: (email) => fetchAPI(`/student/login/${email}`, "GET"),
    scanTranscript: async (file) => {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${BASE_URL}/student/scan-transcript`, {
            method: "POST",
            body: formData
        });
        return await res.json();
    }
};
