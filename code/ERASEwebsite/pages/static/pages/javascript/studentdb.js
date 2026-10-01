// Image cropping logic
const studentDbI18n = document.getElementById('studentdb-i18n').dataset;
let cropper;
const fileInput = document.querySelector("input[name='photo']");
const cropModal = document.getElementById("cropModal");
const cropImage = document.getElementById("cropImage");
const cropSave = document.getElementById("cropSave");
const cropCancel = document.getElementById("cropCancel");

const dropZone = document.getElementById("dropZone");
dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.background = "#e8f2ff";
});

dropZone.addEventListener("dragleave", () => {
    dropZone.style.background = "transparent";
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.background = "transparent";

    const file = e.dataTransfer.files[0];
    if (!file) return;

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;

    const reader = new FileReader();
    reader.onload = function (e) {
        cropImage.src = e.target.result;
        cropModal.style.display = "flex";

        if (cropper) cropper.destroy();
        cropper = new Cropper(cropImage, {
            aspectRatio: 3 / 4,
            viewMode: 1,
            autoCropArea: 1,
            zoomable: false,
            scalable: false,
            movable: false,
            rotatable: false,
            zoomOnWheel: false,
            zoomOnTouch: false,
            cropBoxMovable: true,
            cropBoxResizable: true
        });
    };
    reader.readAsDataURL(file);
});

fileInput.addEventListener("change", function (event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        cropImage.src = e.target.result;
        cropModal.style.display = "flex";

        if (cropper) cropper.destroy();
        cropper = new Cropper(cropImage, {
            aspectRatio: 3 / 4,
            viewMode: 1,
            autoCropArea: 1,
            responsive: true,

            zoomable: false,
            scalable: false,
            movable: false,
            rotatable: false,
            zoomOnWheel: false,
            zoomOnTouch: false,

            cropBoxMovable: true,
            cropBoxResizable: true
        });
    };
    reader.readAsDataURL(file);
});

cropSave.addEventListener("click", function () {
    const canvas = cropper.getCroppedCanvas({
        width: 300,
        height: 400
    });

    canvas.toBlob(function (blob) {
        const newFile = new File([blob], "cropped.jpg", { type: "image/jpeg" });

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(newFile);
        fileInput.files = dataTransfer.files;

        dropZone.style.borderColor = "green";

        cropModal.style.display = "none";
        cropper.destroy();
        
    });
});

cropCancel.addEventListener("click", function () {
    fileInput.value = "";
    cropModal.style.display = "none";
    cropper.destroy();
});

// Live Filtering Logic
const searchInput = document.querySelector(".search-bar input[name='search']");
const genderSelect = document.querySelector(".search-bar select[name='gender']");
const schoolInput = document.querySelector(".search-bar input[name='school']");
const studentCards = document.querySelectorAll(".student-card");

function filterStudents() {
    const nameVal = searchInput.value.toLowerCase();
    const genderVal = genderSelect.value.toLowerCase();
    const schoolVal = schoolInput.value.toLowerCase();

    studentCards.forEach(card => {
        const name = card.querySelector(".student-details div:nth-child(1)").innerText.toLowerCase();
        const gender = card.dataset.gender.toLowerCase();
        const school = card.querySelector(".student-details div:nth-child(3)").innerText.toLowerCase();
        const matchesName = name.includes(nameVal);
        const matchesGender = (genderVal === "" || gender === genderVal);        
        const matchesSchool = school.includes(schoolVal);

        card.style.display = (matchesName && matchesGender && matchesSchool) ? "flex" : "none";
    });
}

searchInput.addEventListener("input", filterStudents);
genderSelect.addEventListener("change", filterStudents);
schoolInput.addEventListener("input", filterStudents);

// Bulk Upload Logic
const bulkModal = document.getElementById('bulkModal');
const openBulkBtn = document.getElementById('openBulkModal');
const cancelBulkBtn = document.getElementById('cancelBulk');
const processBtn = document.getElementById('processBulk');
const previewBody = document.getElementById('previewBody');
const confirmBtn = document.getElementById('confirmBulk');
const finalForm = document.getElementById('finalBulkForm');

let stagedStudents = [];

openBulkBtn.onclick = () => bulkModal.style.display = 'block';
cancelBulkBtn.onclick = () => {
    bulkModal.style.display = 'none';
    stagedStudents = [];
    previewBody.innerHTML = '';
};

processBtn.onclick = async () => {
    const csvFile = document.getElementById('bulkCSV').files[0];
    const zipFile = document.getElementById('bulkZIP').files[0];

    if (!csvFile || !zipFile) return alert(studentDbI18n.selectFiles);

    const zip = await JSZip.loadAsync(zipFile);
    const csvText = await csvFile.text();
    
    const rows = csvText.split('\n').map(row => row.split(','));
    const headers = rows[0].map(h => h.trim().toLowerCase());

    stagedStudents = [];
    previewBody.innerHTML = '';

    for (let i = 1; i < rows.length; i++) {
        if (rows[i].length < 3) continue;
        
        const student = {
            id: Date.now() + i,
            name: rows[i][headers.indexOf('name')]?.trim(),
            gender: rows[i][headers.indexOf('gender')]?.trim(),
            school: rows[i][headers.indexOf('school')]?.trim(),
            imageName: rows[i][headers.indexOf('image')]?.trim(),
            blob: null,
            previewUrl: ''
        };

        const zipEntry = Object.values(zip.files).find(file => file.name.endsWith(student.imageName) && !file.dir);             
        
        if (zipEntry) {
            const blob = await zipEntry.async("blob");
            student.blob = new File([blob], student.imageName, { type: "image/jpeg" });
            student.previewUrl = URL.createObjectURL(blob);
        }

        stagedStudents.push(student);
        renderRow(student);
    }
    confirmBtn.disabled = stagedStudents.length === 0;
};

function renderRow(student) {
    const tr = document.createElement('tr');
    tr.id = `row-${student.id}`;
    tr.style.borderBottom = "1px solid #eee";
    tr.innerHTML = `
        <td><img src="${student.previewUrl}" style="width:50px; height:60px; object-fit:cover; border-radius:5px;"></td>
        <td><input type="text" value="${student.name}" onchange="updateStudent(${student.id}, 'name', this.value)"></td>
        <td><input type="text" value="${student.gender}" style="width:80px" onchange="updateStudent(${student.id}, 'gender', this.value)"></td>
        <td><input type="text" value="${student.school}" onchange="updateStudent(${student.id}, 'school', this.value)"></td>
        <td><button class="btn btn-danger" onclick="removeStaged(${student.id})">${studentDbI18n.delete}</button></td>
    `;
    previewBody.appendChild(tr);
}

function updateStudent(id, field, value) {
    const student = stagedStudents.find(s => s.id === id);
    if (student) student[field] = value;
}

function removeStaged(id) {
    stagedStudents = stagedStudents.filter(s => s.id !== id);
    document.getElementById(`row-${id}`).remove();
    confirmBtn.disabled = stagedStudents.length === 0;
}

finalForm.onsubmit = (e) => {
    stagedStudents.forEach((s, index) => {
        const nameInput = document.createElement('input');
        nameInput.type = 'hidden';
        nameInput.name = `name_${index}`;
        nameInput.value = s.name;
        
        const genderInput = document.createElement('input');
        genderInput.type = 'hidden';
        genderInput.name = `gender_${index}`;
        genderInput.value = s.gender;

        const schoolInput = document.createElement('input');
        schoolInput.type = 'hidden';
        schoolInput.name = `school_${index}`;
        schoolInput.value = s.school;

        finalForm.appendChild(nameInput);
        finalForm.appendChild(genderInput);
        finalForm.appendChild(schoolInput);

        if (s.blob) {
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.name = `photo_${index}`;
            fileInput.style.display = 'none';
            const container = new DataTransfer();
            container.items.add(s.blob);
            fileInput.files = container.files;
            finalForm.appendChild(fileInput);
        }
    });
    
    const countInput = document.createElement('input');
    countInput.type = 'hidden';
    countInput.name = 'bulk_count';
    countInput.value = stagedStudents.length;
    finalForm.appendChild(countInput);
};