document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const formData = new FormData(this);
    const formality = document.querySelector('button[data-formality].active')?.dataset.formality || 'normal';
    const length = document.querySelector('button[data-length].active')?.dataset.length || 'mittel lang';

    formData.append('formality', formality);
    formData.append('length', length);

    const loadingSpinner = document.getElementById('loadingSpinner');
    const mailContent = document.getElementById('mailContent');
    const customerInfo = document.getElementById('customerInfo');
    const sensorStatus = document.getElementById('sensorStatus');
    const additionalFields = document.getElementById('additionalFields');
    const loyaltyField = document.getElementById('loyaltyField');
    const insuranceField = document.getElementById('insuranceField');
    const outlookButton = document.getElementById('outlookButton');

    loadingSpinner.style.display = 'block';
    mailContent.style.display = 'none';
    customerInfo.style.display = 'none';
    sensorStatus.style.display = 'none';
    additionalFields.style.display = 'none';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (response.ok) {
            const customerDetails = `
                <p><strong>Customer ID:</strong> ${result.row_data.customer_id}</p>
                <p><strong>First Name:</strong> ${result.row_data.first_name}</p>
                <p><strong>Last Name:</strong> ${result.row_data.last_name}</p>
                <p><strong>Brand:</strong> ${result.row_data.brand}</p>
                <p><strong>Car Model:</strong> ${result.row_data.model}</p>
                <p><strong>Car Age:</strong> ${result.row_data.car_age}</p>
                <p><strong>Dealer Assignment:</strong> ${result.row_data.dealer_assignment}</p>
                <p><strong>Loyalty Score:</strong> ${result.row_data.lead_score_loyalty}</p>
                <p><strong>Lead Score:</strong> ${result.row_data.lead_score_profit}</p>
            `;
            customerInfo.innerHTML = customerDetails;

            const sensors = [
                { name: 'Engine Oil', value: result.row_data.sensor_engine_oil },
                { name: 'Tire', value: result.row_data.sensor_tire },
                { name: 'Brake Front', value: result.row_data.sensor_break_front },
                { name: 'Brake Back', value: result.row_data.sensor_break_back },
                { name: 'Brake Fluid', value: result.row_data.sensor_break_fluid },
                { name: 'Vehicle Check', value: result.row_data.sensor_vehicle_check },
                { name: 'Inspection', value: result.row_data.sensor_inspection },
                { name: 'Drive Habits', value: result.row_data.sensor_drive_habits }
            ];

            const sensorStatusHTML = sensors.map(sensor => {
                let colorClass;
                switch(sensor.value) {
                    case 1:
                        colorClass = 'dot-green';
                        break;
                    case 2:
                        colorClass = 'dot-yellow';
                        break;
                    case 3:
                        colorClass = 'dot-red';
                        break;
                    default:
                        colorClass = '';
                }
                return `<p><span class="dot ${colorClass}"></span>${sensor.name}</p>`;
            }).join('');

            sensorStatus.innerHTML = sensorStatusHTML;

            loyaltyField.className = `field field-${result.loyalty_field_state}`;
            insuranceField.className = `field field-${result.insurance_field_state}`;

            mailContent.innerHTML = result.mail_content;

            loadingSpinner.style.display = 'none';
            mailContent.style.display = 'block';
            customerInfo.style.display = 'block';
            sensorStatus.style.display = 'block';
            additionalFields.style.display = 'block';
            outlookButton.style.display = 'block';
        } else {
            mailContent.innerText = result.error;
            loadingSpinner.style.display = 'none';
        }
    } catch (error) {
        mailContent.innerText = 'An error occurred while processing your request.';
        loadingSpinner.style.display = 'none';
    }
});

document.querySelectorAll('.formality-btn').forEach(button => {
    button.addEventListener('click', function() {
        document.querySelectorAll('.formality-btn').forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
    });
});

document.querySelectorAll('.length-btn').forEach(button => {
    button.addEventListener('click', function() {
        document.querySelectorAll('.length-btn').forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
    });
});

document.getElementById('outlookButton').addEventListener('click', function() {
    const mailContent = document.getElementById('mailContent').innerText;
    const mailtoLink = `mailto:?body=${encodeURIComponent(mailContent)}`;
    window.location.href = mailtoLink;
});