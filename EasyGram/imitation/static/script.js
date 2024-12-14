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
	send.addEventListener('click', function(){
		let userInput = document.getElementById('inputText')
		if(!userInput.value){
			return alert('Напишите текст')
		}

		let user = document.createElement('div')
		user.classList.add('user')
		user.innerHTML = userInput.value
		history.appendChild(user)

		fetch('/sendMessage', {
			method: 'POST',
			headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({'text': userInput.value})
		}).then(response => response.json()).then(data => {});

		userInput.value = ''
		history.scrollTop = history.scrollHeight
	})
})

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
	let history = document.querySelector('.history')
	let user = document.createElement('div')
	user.classList.add('user')
	user.innerHTML = `/${command}`
	history.appendChild(user)
	history.scrollTop = history.scrollHeight

	fetch('/sendMessage', {
		method: 'POST',
		headers: {
	        'Content-Type': 'application/json',
	    },
	    body: JSON.stringify({'text': `/${command}`})
	}).then(response => response.json()).then(data => {});

	let listCommands = document.querySelector('.listCommands')
	let butt = document.getElementById('showCommands')
	listCommands.style.display = 'none'
	butt.innerText = '/ меню'
}

setInterval(get_response, 1000);
