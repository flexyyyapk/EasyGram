let commands = []

document.addEventListener('DOMContentLoaded', function(){
	fetch('/getCommands', {
		method: 'GET',
		headers: {
            'Content-Type': 'application/json',
        }
	}).then(response => {
		if(response.status === 204) return;
		return response.json()
	}).then(update => {
		commands.push(update)

		let listCommands = document.querySelector('.listCommands')
		console.log(commands)

		update.forEach(command => {
			let buttonCommand = document.createElement('button')
			buttonCommand.onclick = function(){sendCommand(command.command)}
			buttonCommand.innerHTML = `<b>${command.command}</b> - ${command.description}`
			buttonCommand.classList.add('command')
			listCommands.appendChild(buttonCommand)
		})
	})

	fetch('/getBotData', {
		method: 'GET',
		headers: {
            'Content-Type': 'application/json',
        }
	}).then(response => {
		if(response.status === 204) return;
		return response.json()
	}).then(data => {
		let name = document.getElementById('name')
		let username = document.getElementById('username')
		let description = document.getElementById('description')
		let ava = document.getElementById('photo')

		name.innerText = data.name
		username.innerText = `@${data.username}`

		if(data.description){
			description.innerText = data.description
		}else{
			description.innerText = 'Имитированный бот🤖'
		}
		if(data.image){
			ava.style.background = `url(${data.image}) center no-repeat, linear-gradient(135deg, #6cb2f7, #b3dafe)`
			ava.style.backgroundSize = 'cover'
		}
	})

	let history = document.querySelector('.history')
	let send = document.getElementById('sendMessage')

	document.addEventListener('keydown', function(event){
		let userInput = document.getElementById('inputText')
		if(event.ctrlKey && event.key === 'Enter' && document.activeElement === userInput){
			sendMessage()
		}
	})

	send.addEventListener('click', function(){
		sendMessage()
	})
})

function sendMessage(message){
	console.log(message)
	let userInput = document.getElementById('inputText')
	let history = document.querySelector('.history')

	if(!userInput.value && message === undefined){
		return alert('Напишите текст')
	}

	let user = document.createElement('div')
	user.classList.add('user')
	user.innerHTML = userInput.value ? userInput.value : message

	fetch('/sendMessage', {
		method: 'POST',
		headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({'text': userInput.value ? userInput.value : message})
	}).then(response => response.json()).then(data => {
		let message_id = data.message_id
		user.id = `${message_id}`
	});

	history.appendChild(user)
	userInput.value = ''
	history.scrollTop = history.scrollHeight
}

function get_response() {
	let history = document.querySelector('.history');

	fetch('/getUpdates', {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
		},
	}).then(response => {
		if (response.status === 204) return;
		return response.json();
	}).then(data => {
		if (data && data.updates) {
			data.updates.forEach(update => {
				if('message' in update){
					let bot = document.createElement('div');
					bot.classList.add('bot');
					bot.id = `${update.message.message_id}`

					if(update.message.parse_mode == 'html'){
						bot.textContent = update.message.text;
					}else if(update.message.parse_mode == 'markdown'){
						bot.textContent = update.message.text
					}else{
						bot.innerText = update.message.text
					}
					history.appendChild(bot)

					history.scrollTop = history.scrollHeight
				}else if('set_commands' in update){
					commands.push(update.set_commands)

					let listCommands = document.querySelector('.listCommands')
					console.log(commands)

					update.set_commands.forEach(command => {
						let buttonCommand = document.createElement('button')
						buttonCommand.onClick = `sendCommand(${command.command})`
						buttonCommand.innerHTML = `<b>${command.command}</b> - ${command.description}`
						buttonCommand.classList.add('command')
						listCommands.appendChild(buttonCommand)
					})
				}else if('photo' in update){
					let bot = document.createElement('div')
					bot.classList.add('bot')
					bot.id = `${update.photo.message_id}`

					let img = document.createElement('img')
					img.src = `data:image/jpeg;base64,${update.photo.photo}`
					img.alt = 'Фото'
					img.style.width = '95%'
					img.style.height = 'auto'
					img.style.borderRadius = '10px'
					img.style.margin = '10px'
					img.style.objectFit = 'cover'
					img.style.objectPosition = 'center'
					img.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)'
					img.style.transition = 'transform 0.3s ease'
					img.style.cursor = 'pointer'
					bot.appendChild(img)

					if(update.photo.caption){
						let caption = document.createElement('div')
						caption.id = 'caption'
						caption.textContent = update.photo.caption
						bot.appendChild(caption)
					}

					history.appendChild(bot)
				}else if('delete_message' in update){
					let message = document.getElementById(update.delete_message.message_id.toString())
					if(message){
						message.remove()
					}
				}else if('edit_message_text' in update){
					let message = document.getElementById(update.edit_message_text.message_id.toString())
					if(message){
						let parent_msg = message.querySelector('#caption')

						if(parent_msg){
							parent_msg.textContent = update.edit_message_text.text
						}else{
							message.textContent = update.edit_message_text.text
						}

						let status = document.createElement('div')
						status.textContent = 'изменено'
						status.style.color = 'gray'
						status.style.fontSize = '12px'
						message.appendChild(status)
					}
				}else if('poll' in update){
					let bot = document.createElement('div')
					bot.classList.add('bot')
					bot.id = `${update.poll.message_id}`
					bot.innerHTML = `<h4>${update.poll.question}</h4>`

					bot.innerHTML += `<br>`
					
					if(!update.poll.allows_multiple_answers){
						update.poll.options.forEach(option => {
							let input = document.createElement('input')
							input.innerText = option.text
							input.type = 'radio'
							input.name = `poll_${update.poll.message_id}`
							input.value = option.text
							input.id = `poll_${update.poll.message_id}_${option.text}`
							
							let label = document.createElement('label')
							label.for = `poll_${update.poll.message_id}_${option.text}`
							label.textContent = option.text
							
							bot.appendChild(input)
							bot.appendChild(label)
							bot.innerHTML += `<br>`
						})
					}else{
						for(let i = 0; i < update.poll.options.length; i++){
							let input = document.createElement('input')
							input.innerText = update.poll.options[i].text
							input.type = 'checkbox'
							input.name = `poll_${update.poll.message_id}_${i}`
							input.value = update.poll.options[i].text
							input.id = `poll_${update.poll.message_id}_${i}`
							
							let label = document.createElement('label')
							label.for = `poll_${update.poll.message_id}_${i}`
							label.textContent = update.poll.options[i].text

							bot.appendChild(input)
							bot.appendChild(label)
							bot.innerHTML += `<br>`
						}
					}

					history.appendChild(bot)
				}
			});
		}
	}).catch(err => console.error('Ошибка при получении обновлений:', err));
}

function showCommands(){
	if(!commands){
		return;
	}

	let listCommands = document.querySelector('.listCommands')
	let butt = document.getElementById('showCommands')

	if(listCommands.style.display == 'none'){
		listCommands.style.display = 'block'
		butt.innerText = '× меню'
	}else{
		listCommands.style.display = 'none'
		butt.innerText = '/ меню'
	}
}

function sendCommand(command){
	sendMessage(`/${command}`)

	let listCommands = document.querySelector('.listCommands')
	let butt = document.getElementById('showCommands')
	listCommands.style.display = 'none'
	butt.innerText = '/ меню'
}

setInterval(get_response, 1000);