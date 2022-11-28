test:
	bashful run run.bashful.yaml

boxes:
	bashful run build-boxes.bashful.yaml

clean:
	-rm -r .bashful/
	-rm -r build/
	-rm -r copyfs/out
	-rm copyfs/test_template*.sh
	-rm -r ext4/out
	-rm ext4/test_template*.sh
	-rm -r nilfs/out
	-rm nilfs/test_template*.sh
	-rm -r waybackfs/out
	-rm waybackfs/test_template*.sh