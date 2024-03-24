<script lang="ts">
    import DegreeSelector from "$lib/components/DegreeSelector.svelte";
	import SelectedCourses from "$lib/components/SelectedCourses.svelte";
    import YearSelector from "$lib/components/YearSelector.svelte";
</script>

<div class="flex items-center justify-center h-screen w-screen">
    <div class="w-full h-full p-12">
      <!-- Your content here -->
      <div class="w-full h-full outline outline-1">
        <div class="w-full h-full flex flex-row">
            <div class="w-1/3 h-full bg-blue-200 p-12 flex flex-col">
                <div class="w-full h-2/5 bg-blue-100 flex flex-col">
                    <div class="w-full h-1/2 bg-green-300 flex flex-row">
                        <div class="w-1/2 h-full flex">
                            <DegreeSelector />
                        </div>
                        <div class="w-1/2 h-full bg-green-500 flex">
                            <YearSelector />
                        </div>
                    </div>
                    <div class="w-full h-1/2 bg-red-300">
                        <SelectedCourses />
                    </div>
                </div>
                <div class="w-full h-3/5 bg-blue-300"></div>
            </div>
            <div class="w-2/3 h-full bg-blue-300"></div>
        </div>
      </div>
    </div>
  </div>
