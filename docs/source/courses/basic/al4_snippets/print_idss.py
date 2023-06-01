from imas.ids_names import IDSName

# As each imas module is compiled with a specific DD version, we can load the
# names from the module itself
print([name.value for name in IDSName])
