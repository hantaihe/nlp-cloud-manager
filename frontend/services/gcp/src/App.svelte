<script lang="ts">
	import BillingDashboard from './lib/components/BillingDashboard.svelte';
	import './app.css';
</script>

<main>
	<div class="background-blobs">
		<div class="blob blob-1"></div>
		<div class="blob blob-2"></div>
		<div class="blob blob-3"></div>
	</div>

	<BillingDashboard />
</main>

<style>
	main {
		position: relative;
		min-height: 100vh;
		overflow-x: hidden;
	}

	.background-blobs {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		z-index: -1;
		overflow: hidden;
		filter: blur(80px);
		opacity: 0.15;
	}

	.blob {
		position: absolute;
		border-radius: 50%;
	}

	.blob-1 {
		width: 400px;
		height: 400px;
		background: #4285f4;
		top: -100px;
		right: -100px;
		animation: move 20s infinite alternate;
	}

	.blob-2 {
		width: 300px;
		height: 300px;
		background: #34a853;
		bottom: -50px;
		left: -50px;
		animation: move 15s infinite alternate-reverse;
	}

	.blob-3 {
		width: 250px;
		height: 250px;
		background: #fbbc04;
		top: 40%;
		left: 20%;
		animation: move 25s infinite alternate;
	}

	@keyframes move {
		from {
			transform: translate(0, 0);
		}
		to {
			transform: translate(50px, 50px);
		}
	}
</style>
