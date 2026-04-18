const auth = {
    saveProfile: (data) => {
        localStorage.setItem("edupath_profile", JSON.stringify(data));
    },
    saveStudentId: (id) => {
        localStorage.setItem("edupath_student_id", id);
    },
    getProfile: () => {
        const p = localStorage.getItem("edupath_profile");
        return p ? JSON.parse(p) : null;
    },
    getStudentId: () => {
        return localStorage.getItem("edupath_student_id");
    },
    isLoggedIn: () => {
        return !!localStorage.getItem("edupath_student_id");
    },
    checkAuthAndRedirect: () => {
        if (!auth.isLoggedIn()) {
            window.location.href = "onboarding.html";
        }
    },
    logout: () => {
        localStorage.clear();
        window.location.href = "index.html";
    }
};
